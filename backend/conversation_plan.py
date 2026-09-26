"""Shared, provider-independent conversation planning over the public schema.

Entity IDs always come from the current catalog. Intent configuration supplies
routing hints, never SQL or factual evidence. No account/report data is eligible.
"""
from dataclasses import dataclass, field
import re
from types import SimpleNamespace
from sqlalchemy import select
from .db import MODELS
from .query_understanding import canonical, resolve, topic, general_topic, YEAR, STUDY, TERM
from .career_scope import career_names, broad_career_question

PUBLIC_TABLES = ('majors', 'curricula', 'careers', 'general', 'news')
TITLE_FIELDS = dict(majors='major_name_th', curricula='degree_name', careers='job_title', general='topic', news='title')


@dataclass(frozen=True)
class TopicSpec:
    key: str
    tables: tuple
    cues: tuple
    label: str


# Schema vocabulary is declared in one registry. New records are discovered
# from the catalog; no record IDs or factual answers live in these descriptors.
TOPICS = (
    TopicSpec('tuition', ('curricula',), ('ค่าเทอม', 'ค่าเล่าเรียน', 'ค่าธรรมเนียม', 'ค่าใช้จ่ายในการเรียน'), 'ค่าเทอม'),
    TopicSpec('scholarship', ('general',), ('ทุน', 'กยศ', 'กู้เรียน', 'กู้ค่าเรียน'), 'ทุนการศึกษา'),
    TopicSpec('admissions', ('general', 'news'), ('สมัคร', 'คุณสมบัติผู้สมัคร', 'เอกสารสมัคร'), 'วิธีสมัคร'),
    TopicSpec('staff', ('general',), ('อาจารย์', 'บุคลากร'), 'บุคลากร'),
    TopicSpec('services', ('general',), ('บริการนักศึกษา', 'บริการให้นักศึกษา'), 'บริการนักศึกษา'),
    TopicSpec('career', ('careers', 'curricula'), ('อาชีพ', 'ทำงาน', 'จบไป', 'เงินเดือน', 'รายได้', 'ค่าตอบแทน', 'ทักษะ', 'ทำเว็บ'), 'อาชีพ'),
    TopicSpec('news', ('news',), ('ข่าว', 'กิจกรรม', 'โครงการ', 'อบรม', 'open house'), 'ข่าว'),
    TopicSpec('contact', ('general', 'majors'), ('ติดต่อ', 'เบอร์โทร', 'โทรศัพท์', 'อีเมล', 'ที่อยู่', 'ตั้งอยู่'), 'ติดต่อ'),
    TopicSpec('history', ('general',), ('ประวัติคณะ', 'ก่อตั้ง', 'ความเป็นมา'), 'ประวัติคณะ'),
    TopicSpec('mission', ('general',), ('วิสัยทัศน์', 'พันธกิจ'), 'วิสัยทัศน์'),
    TopicSpec('curriculum', ('curricula', 'majors', 'general'), ('หลักสูตร', 'หน่วยกิต', 'เทอม', 'ภาคเรียน', 'เรียนอะไร', 'เรียนกี่ปี', 'แผนการเรียน', 'สาขา', 'รายวิชา', 'แนะนำ', 'สนใจ', 'ถนัด'), 'หลักสูตร'),
)
REGISTRY = {item.key: item for item in TOPICS}
FIELD_CUES = {
    'salary_start': ('เงินเดือน', 'รายได้', 'ค่าตอบแทน'),
    'skill_required': ('ทักษะ',), 'tuition_fee': ('ค่าเทอม', 'ค่าเล่าเรียน', 'ค่าธรรมเนียม'),
    'total_credits': ('หน่วยกิต',), 'tel': ('เบอร์โทร', 'โทรศัพท์'),
    'email': ('อีเมล',), 'website_url': ('เว็บไซต์',),
    'content': ('เมื่อไหร่', 'วันไหน', 'ที่ไหน', 'รายละเอียด'),
}

ACK = re.compile(r'(?:ขอบคุณ|โอเค|เข้าใจแล้ว|ครับ|ค่ะ|คะ)[ !?.]*(?:ครับ|ค่ะ|คะ)?[ !?.]*')
REFERENCES = ('กี่', 'นี้', 'นั้น', 'เดิม', 'เพิ่มเติม', 'รายละเอียด', 'อีก', 'ที่ไหน', 'เมื่อไหร่', 'วันไหน', 'เท่าไหร่', 'เท่าไร', 'อะไรบ้าง', 'อย่างไร', 'ยังไง')


@dataclass(frozen=True)
class Entity:
    table: str
    id: int
    title: str


@dataclass
class QueryPlan:
    raw: str
    query: str
    route: str | None = None
    entities: tuple = ()
    major_names: tuple = ()
    allowed_tables: tuple = PUBLIC_TABLES
    clarification: str | None = None
    transition: str = 'new'
    intent_id: int | None = None
    intent_context: str = ''
    static_response: str | None = None
    year: str | None = None
    study_year: str | None = None
    term: str | None = None
    requested_fields: tuple = ()
    intent_candidates: tuple = field(default=(), repr=False)
    general_scope_resolved: bool = False


class PlannedQuery(str):
    def __new__(cls, plan):
        obj = super().__new__(cls, plan.query)
        obj.plan = plan
        return obj


@dataclass
class Catalog:
    majors: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    intents: list = field(default_factory=list)

    @classmethod
    def load(cls, db):
        majors = list(db.scalars(select(MODELS['majors'])))
        entities = [Entity('majors', m.id, m.major_name_th) for m in majors]
        for table in PUBLIC_TABLES[1:]:
            model = MODELS[table]
            # Read catalog identities, not all documents or private user rows.
            from sqlalchemy.orm import load_only
            rows = db.scalars(select(model).options(load_only(model.id, getattr(model, TITLE_FIELDS[table]))))
            entities.extend(Entity(table, row.id, getattr(row, TITLE_FIELDS[table]) or '') for row in rows)
        intents = list(db.scalars(select(MODELS['intents']).where(MODELS['intents'].is_active == True).order_by(MODELS['intents'].id)))
        return cls(majors, entities, intents)

    @property
    def career_titles(self):
        return [e.title for e in self.entities if e.table == 'careers']


def detect_route(q):
    for spec in TOPICS:
        if any(cue in q.lower() for cue in spec.cues):
            if spec.key == 'admissions' and any(cue in q for cue in ('ข่าว', 'ประกาศ')):
                return 'news'
            return spec.key
    return None


def named_entities(q, catalog):
    careers = set(career_names(q, catalog.career_titles))
    result = []
    from .structured_evidence import named_news
    event_ids = {e.id for e in named_news(q, [e for e in catalog.entities if e.table == 'news'])} if detect_route(q) in (None, 'news') else set()
    for entity in catalog.entities:
        title = canonical(entity.title).lower()
        if entity.table == 'majors' or not title:
            continue
        matched = title in q.lower() or entity.table == 'careers' and entity.title in careers
        if entity.table == 'news':
            matched |= entity.id in event_ids
            # Distinct English event names come from stored titles, not a
            # hardcoded Smart Start/Open House ID. Generic suffixes don't count.
            names = re.findall(r'[a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*', entity.title)
            matched |= any(n.lower() in q.lower() and n.lower() not in ('science pcru', 'science') and len(n) >= 6 for n in names)
        if entity.table == 'curricula' and ('หลักสูตร' not in q or len(title) < 16):
            matched = False
        if matched:
            result.append(entity)
    # A uniquely named event takes precedence over general topic words inside
    # its title, but explicit salary/tuition questions do not become news.
    return result


def choose_intent(q, intents):
    ranked = []
    static_matches = []
    for intent in intents:
        if not intent.is_active:
            continue
        keywords = [canonical(x.strip()).lower() for x in (intent.prompt_context or '').split(',') if x.strip()]
        if intent.action_type == 'rule_based':
            if intent.static_response and any(re.fullmatch(re.escape(k) + r'[ !?.]*(?:ครับ|ค่ะ|คะ)?[ !?.]*', q.lower()) for k in keywords):
                static_matches.append(intent)
        elif intent.action_type == 'rag':
            score = sum(len(k) for k in keywords if k in q.lower())
            # A free-form description is not a comma-separated keyword list.
            # The stored intent name can still provide an exact match.
            name = canonical(intent.intent_name or '').lower()
            if name and name in q.lower():
                score += len(name)
            if score:
                ranked.append((score, intent))
    if static_matches:
        return static_matches[0] if len(static_matches) == 1 else None
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked and (len(ranked) == 1 or ranked[0][0] > ranked[1][0]) else None


def make_plan(q, history, catalog):
    active = None
    frames = {}
    last_sources = ()
    turns = list(history) + [SimpleNamespace(user_query=q)]
    for index, turn in enumerate(turns):
        current = canonical(turn.user_query)
        if ACK.fullmatch(current) and index < len(turns)-1:
            continue
        named = tuple(m.major_name_th for m in catalog.majors if m.major_name_th in current)
        explicit = named_entities(current, catalog)
        route = detect_route(current)
        if named and route is None or re.search(r'\b[A-Z]{4}\d{4}\b', current):
            route = 'curriculum'
        if any(e.table == 'careers' for e in explicit) and route is None:
            route = 'career'
        if any(e.table == 'news' for e in explicit) and route not in ('career', 'tuition'):
            route = 'news'
        if any(e.table == 'general' for e in explicit) and route is None:
            route = 'general'
        broad = any(x in current for x in ('ทั้งคณะ', 'ของคณะ', 'ทุกสาขา', 'คณะมี', 'คณะตั้ง'))
        reference = any(x in current for x in REFERENCES) or current.startswith('แล้ว')
        returning = any(x in current for x in ('กลับมา', 'กลับไป', 'เรื่องเดิม'))
        old = frames.get(route) if returning and route in frames else active
        if route is None and reference and old:
            route = old.route
        # Place/time questions about an event retain that event, not faculty
        # contact details. A literal contact request is an explicit topic switch.
        if old and old.route == 'news' and not explicit and not broad and any(x in current for x in ('จัดที่ไหน', 'จัดวันไหน', 'จัดเมื่อไหร่', 'ที่ไหน', 'วันไหน')):
            route = 'news'
        if old and old.entities and not broad and not named and route == 'contact' and any(x in current for x in ('นี้', 'นั้น', 'ติดต่อใคร')):
            route = old.route
        if old and not broad and any(x in current for x in ('กี่บาท', 'ราคาเท่าไหร่')) and route is None:
            route = 'career' if old.route == 'career' else 'tuition' if old.route in ('curriculum', 'tuition') else old.route
        spec = REGISTRY.get(route)
        tables = spec.tables if spec else ('general',) if route == 'general' else PUBLIC_TABLES
        compatible = old and route == old.route and not broad and not (named and named != old.major_names)
        entities = tuple(e for e in explicit if e.table in tables and (route != 'career' or e.table == 'careers'))
        requested_years = re.findall(YEAR, current)
        if requested_years:
            entities = tuple(e for e in entities if e.table != 'news' or not re.findall(YEAR, e.title) or requested_years[0] in e.title)
        if not entities and compatible and reference:
            if route == 'news' and requested_years and old.year and requested_years[0] != old.year:
                names = [n for e in old.entities for n in re.findall(r'[a-zA-Z]{3,}(?:\s+[a-zA-Z]{3,})*', e.title)]
                entities = tuple(e for e in catalog.entities if e.table == 'news' and requested_years[0] in e.title and any(n.lower() in e.title.lower() for n in names))
                if names:
                    current += ' ' + names[0]
            else:
                entities = old.entities
        if route == 'career' and broad_career_question(current):
            entities = ()
        arithmetic = bool(re.search(r'\d+\s*[+*/=]\s*\d+', current))
        clarification = 'คำถามนี้อยู่นอกข้อมูลแนะแนวของคณะ กรุณาสอบถามเรื่องคณะ หลักสูตร อาชีพ หรือการสมัครค่ะ' if arithmetic else 'ต้องการสอบถามข้อมูลด้านใดของคณะหรือสาขาวิชาคะ' if route is None and not explicit and not named and not ACK.fullmatch(current) else None
        ordinal = re.search(r'(?:อัน|รายการ|ข่าว|อาชีพ)(?:ที่)?(แรก|หนึ่ง|สอง|สาม|\d+)', current)
        if ordinal:
            token = ordinal[1]
            n = {'แรก': 1, 'หนึ่ง': 1, 'สอง': 2, 'สาม': 3}.get(token, int(token) if token.isdigit() else 0)
            choices = [e for e in last_sources if e.table in tables]
            if 0 < n <= len(choices):
                entities = (choices[n-1],)
            else:
                clarification = 'กรุณาระบุชื่อรายการที่ต้องการสอบถาม เพื่อให้เลือกข้อมูลได้ตรงค่ะ'
        general_scope_resolved = not entities and 'general' in tables and route not in ('curriculum', 'news')
        if general_scope_resolved:
            scope_names = named or (() if broad else old.major_names if old else ())
            candidates = [e for e in catalog.entities if e.table == 'general' and detect_route(canonical(e.title)) == route]
            if scope_names:
                candidates = [e for e in candidates if all(name in canonical(e.title) for name in scope_names)]
            else:
                candidates = [e for e in candidates if not any(m.major_name_th in canonical(e.title) for m in catalog.majors)]
            entities = tuple(candidates)
        prior = [SimpleNamespace(user_query=old.query)] if old and not broad else []
        expanded = resolve(current, prior, catalog.majors, catalog.career_titles)
        if broad:
            names = named
        elif named:
            names = named
        elif route == 'news' and explicit:
            names = ()
        else:
            names = old.major_names if old else ()
        if route in ('scholarship', 'staff', 'admissions', 'services') and not names and not entities and not broad:
            clarification = 'ต้องการทราบข้อมูลของสาขาวิชาไหนคะ'
        # Expand only compatible slots. Never carry a previous event year into
        # a new subject or silently inject the first of multiple majors.
        if old and route != old.route and route not in ('curriculum', 'tuition'):
            expanded = current
        for name in names:
            if name not in expanded:
                expanded = name + ' ' + expanded
        if route and route not in ('curriculum', 'tuition') and entities:
            for entity in entities:
                if entity.title not in expanded:
                    expanded += ' ' + entity.title
        if route == 'career' and any(x in current for x in ('กี่บาท', 'ราคาเท่าไหร่')):
            expanded += ' เงินเดือน'
        if route and route in REGISTRY and detect_route(expanded) is None:
            expanded += ' ' + REGISTRY[route].label
        years = re.findall(YEAR, current)
        if years and entities:
            entities = tuple(e for e in entities if e.table != 'news' or not re.findall(YEAR, e.title) or years[0] in e.title)
        if len(entities) > 1 and (reference and not explicit) and not any(x in current for x in ('ทั้งหมด', 'แต่ละ', 'ล่าสุด', 'เปรียบเทียบ')):
            clarification = 'หมายถึงรายการไหนคะ: ' + ' หรือ '.join(e.title for e in entities[:5])
        plan = QueryPlan(q, expanded, route, entities, names, tables, clarification,
                         'return' if returning else 'continue' if compatible else 'switch' if active else 'new')
        plan.general_scope_resolved = general_scope_resolved
        plan.year = (re.search(YEAR, expanded).group(1) if re.search(YEAR, expanded) else None)
        plan.study_year = (re.search(STUDY, expanded).group(1) if re.search(STUDY, expanded) else None)
        plan.term = (re.search(TERM, expanded).group(1) if re.search(TERM, expanded) else None)
        plan.requested_fields = tuple(field for field, words in FIELD_CUES.items() if any(w in current for w in words))
        if set(plan.requested_fields) & {'salary_start', 'skill_required'} and set(plan.requested_fields) & {'tuition_fee', 'total_credits'}:
            plan.clarification = 'คำถามมีทั้งข้อมูลหลักสูตรและข้อมูลอาชีพ ต้องการทราบเรื่องหลักสูตรหรืออาชีพก่อนคะ'
        active = plan
        if route:
            frames[route] = plan
        # Only record identities from this session; never trust old answer text
        # as facts. Deleted records cannot be selected through an ordinal.
        last_sources = tuple(e for source in getattr(turn, 'sources', ()) or ()
                             for e in catalog.entities if source.get('url') == f'/records/{e.table}/{e.id}')
        if last_sources and index < len(turns)-1 and not plan.entities:
            compatible_sources = tuple(e for e in last_sources if e.table in plan.allowed_tables)
            if compatible_sources:
                plan.entities = compatible_sources
    selected = choose_intent(canonical(q), catalog.intents) or choose_intent(active.query, [i for i in catalog.intents if i.action_type == 'rag'])
    active.intent_candidates = tuple(catalog.intents)
    if selected:
        active.intent_id = selected.id
        active.intent_context = selected.prompt_context or ''
        if selected.action_type == 'rule_based':
            active.static_response = selected.static_response
    return active
