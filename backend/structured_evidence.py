"""Retrieve existing managed facts without treating unrelated PDFs as evidence."""
import re
from datetime import date
from difflib import SequenceMatcher
from sqlalchemy import select
from .db import MODELS, CurriculumCareer, Document
from .query_understanding import topic, YEAR, mentioned_majors, whole_curriculum, general_topic


def source(title, url, content):
    return dict(title=title, url=url, text=content, document_id=None,
                chunk_id=None, similarity=1.0)


def published_date(content):
    """Only explicit publication labels qualify; event/import dates do not."""
    months = 'มกราคม กุมภาพันธ์ มีนาคม เมษายน พฤษภาคม มิถุนายน กรกฎาคม สิงหาคม กันยายน ตุลาคม พฤศจิกายน ธันวาคม'.split()
    match = re.search(r'(?:โพสต์เมื่อ|เผยแพร่เมื่อ|วันที่เผยแพร่)\s*:?\s*(\d{1,2})\s+(' + '|'.join(months) + r')\.?\s+(25\d{2}|20\d{2})', content or '')
    if not match:
        numeric = re.search(r'(?:โพสต์เมื่อ|เผยแพร่เมื่อ|วันที่เผยแพร่)\s*:?\s*(\d{1,2})/(\d{1,2})/(25\d{2}|20\d{2})', content or '')
        if not numeric:
            return None
        day, month, year = map(int, numeric.groups())
        try:
            return date(year - (543 if year >= 2500 else 0), month, day)
        except ValueError:
            return None
    day, month, year = match.groups()
    try:
        return date(int(year) - (543 if int(year) >= 2500 else 0), months.index(month)+1, int(day))
    except ValueError:
        return None


def named_news(q, rows):
    """Resolve stored event titles without requiring the word 'news'."""
    def compact(value):
        return re.sub(r'[\W_\d]+', '', value.lower())
    def distinct(value):
        for word in ['คณะวิทยาศาสตร์และเทคโนโลยี', 'มหาวิทยาลัยราชภัฏเพชรบูรณ์',
                     'วิทยาการคอมพิวเตอร์', 'ข่าวประชาสัมพันธ์', 'SCIENCE PCRU']:
            value = value.replace(word, '')
        return compact(value)
    query = distinct(q)
    found = []
    for row in rows:
        names = re.findall(r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,})*', row.title)
        english_match = any(len(compact(name)) >= 6 and compact(name) in query
                            for name in names if compact(name) != 'sciencepcru')
        shared = SequenceMatcher(None, query, distinct(row.title), autojunk=False).find_longest_match()
        if english_match or shared.size >= 14:
            found.append(row)
    return found


def retrieve_managed(db, q, majors, curricula):
    """None delegates to semantic search; [] means this route has no evidence."""
    kind = topic(q.lower())
    named = mentioned_majors(q, majors)
    year = re.search(YEAR, q)
    year = year.group(1) if year else None
    major = named[0] if len(named) == 1 else None
    news_rows = list(db.scalars(select(MODELS['news']).order_by(MODELS['news'].id.desc())))
    event_rows = named_news(q, news_rows)
    if event_rows:
        kind = 'news'
    # Prefer the matching managed topic over loosely similar curriculum chunks.
    # Scope by the major explicitly named in the stored topic, never all majors.
    if major and not event_rows:
        groups = [('ทุน', 'ทุนการศึกษา'), ('บริการนักศึกษา', 'บริการนักศึกษา'),
                  ('บุคลากร', 'บุคลากร'), ('อาจารย์', 'บุคลากร'),
                  ('ติดต่อ', 'ติดต่อ'), ('ขั้นตอนการสมัคร', 'สมัคร'),
                  ('วิธีสมัคร', 'สมัคร')]
        wanted = [title_word for query_word, title_word in groups if query_word in q]
        if general_topic(q):
            wanted.append(general_topic(q))
        if wanted:
            rows = db.scalars(select(MODELS['general'])).all()
            selected = [r for r in rows if major.major_name_th in r.topic
                        and any(word in r.topic for word in wanted)]
            if selected:
                if year:
                    selected = [r for r in selected if year in r.topic + ' ' + (r.description or '')]
                return [source(r.topic, f'/records/general/{r.id}', r.description or '') for r in selected]
    if not named and any(t in q for t in ['สาขาอะไร', 'สาขาไหน', 'กี่สาขา', 'หลักสูตรอะไร', 'หลักสูตรไหน']):
        return [source('ข้อมูลสาขาวิชาในระบบ', '/records/overview',
                       f'ข้อมูลสาขาที่จัดเก็บในระบบมี {len(majors)} รายการ:\n' + '\n'.join(m.major_name_th for m in majors))]
    matching = [c for c in curricula if major and c.major_id == major.id and (not year or str(c.curriculum_year) == year)]
    # A broad introduction should use managed descriptions, not a random PDF
    # appendix. Specific questions retain their existing retrieval routes.
    introduction = any(w in q for w in ['เกี่ยวกับ', 'แนะนำ', 'ขอข้อมูล', 'รู้จัก', 'ข้อมูลทั่วไป'])
    specific = any(w in q for w in ['เทอม', 'ภาคเรียน', 'หน่วยกิต', 'วิชาอะไร', 'เรียนอะไร',
        'เรียนเกี่ยวกับอะไร', 'ค่าเทอม', 'ค่าธรรมเนียม', 'อาชีพ', 'ทำงาน', 'ทุน',
        'อาจารย์', 'บุคลากร', 'ติดต่อ', 'สมัคร', 'ข่าว', 'กิจกรรม', 'เงินเดือน'])
    if major and introduction and kind == 'curriculum' and not general_topic(q) and not specific and not event_rows:
        descriptions = [c for c in matching if (c.description or '').startswith('ข้อมูลจากหน้าแนะนำสาขาวิชา:')]
        if descriptions:
            return [source(c.degree_name, f'/records/curricula/{c.id}', c.description) for c in descriptions]
        if year:
            return [source(c.degree_name, f'/records/curricula/{c.id}',
                           f'{c.degree_name}\n{c.description or ""}') for c in matching]
        return [source(major.major_name_th, f'/records/majors/{major.id}',
                       f'{major.major_name_th}\n{major.description or ""}')]
    if kind == 'curriculum' and whole_curriculum(q) and major:
        return [source(c.degree_name, f'/records/curricula/{c.id}',
                       f'{major.major_name_th} ปีตามรายการหลักสูตร {c.curriculum_year} หน่วยกิตรวมตลอดหลักสูตร {c.total_credits} หน่วยกิต ตามข้อมูลที่เจ้าหน้าที่บันทึก ไม่ใช่หน่วยกิตรายเทอม\nคำอธิบายรายการ: {c.description or ""}')
                for c in matching if c.total_credits is not None]
    if kind == 'tuition':
        return [source(c.degree_name, f'/records/curricula/{c.id}',
                       f'ข้อมูลที่เจ้าหน้าที่บันทึก: {c.degree_name} ช่องปีหลักสูตร {c.curriculum_year} '
                       f'ค่าธรรมเนียมการศึกษาต่อภาคเรียน {c.tuition_fee} บาท ไม่รวมค่าใช้จ่ายอื่นที่ไม่ได้ระบุ')
                for c in matching if c.tuition_fee is not None]
    if kind == 'career' and major:
        # An explicit curriculum year can use the complete career section in
        # the uploaded curriculum, rather than a partially populated registry.
        if year and not any(w in q for w in ['เงินเดือน', 'ทักษะ', 'รายได้']):
            evidence = []
            for c in matching:
                doc = db.scalar(select(Document).where(Document.record_type == 'curricula', Document.record_id == c.id))
                section = re.search(r'(?m)^\s*(\d+)\.\s*อาชีพที่[^\n]*\n((?:\s*\1\.\d+[^\n]*\n?)+)', doc.content or '') if doc else None
                if section:
                    evidence.append(source(c.degree_name, f'/records/curricula/{c.id}',
                        f'{c.degree_name} ปีหลักสูตร {c.curriculum_year}\n' + section.group(0).strip()))
            if evidence:
                return evidence
        sources = []
        for c in matching:
            jobs = db.scalars(select(MODELS['careers']).join(CurriculumCareer,
                CurriculumCareer.career_id == MODELS['careers'].id).where(CurriculumCareer.curriculum_id == c.id)).all()
            for job in jobs:
                content = f'{c.degree_name} ปีตามรายการหลักสูตร {c.curriculum_year}\nอาชีพ: {job.job_title}\n{job.job_description or ""}'
                if job.salary_start is not None:
                    content += f'\nเงินเดือนเริ่มต้นตามข้อมูลที่บันทึก {job.salary_start} บาท ไม่ใช่การรับประกันรายได้'
                if job.skill_required:
                    content += '\nทักษะที่จำเป็น: ' + job.skill_required
                sources.append(source(job.job_title, f'/records/careers/{job.id}', content))
        if sources:
            grouped = {}
            for item in sources:
                if item['url'] in grouped:
                    grouped[item['url']]['text'] += '\n\n' + item['text']
                else:
                    grouped[item['url']] = item
            return list(grouped.values())
        return None
    if kind in ['contact', 'history', 'mission'] and not major:
        words = {'contact': ['ติดต่อ'], 'history': ['ประวัติ'], 'mission': ['วิสัยทัศน์', 'พันธกิจ']}[kind]
        rows = db.scalars(select(MODELS['general'])).all()
        return [source(r.topic, f'/records/general/{r.id}', r.description or '') for r in rows if any(w in r.topic for w in words)]
    if kind == 'contact' and major:
        fields = [('โทรศัพท์', major.tel), ('อีเมล', major.email), ('เว็บไซต์', major.website_url), ('Facebook', major.facebook_page)]
        values = [f'{k}: {v}' for k, v in fields if v]
        return [source(major.major_name_th, f'/records/majors/{major.id}', '\n'.join(values))] if values else []
    if kind == 'news':
        rows = event_rows if event_rows else news_rows
        if year:
            rows = [r for r in rows if year in (r.title + ' ' + (r.content or ''))]
        if major:
            rows = [r for r in rows if major.major_name_th in r.title + ' ' + (r.content or '')]
        # Exact named events and admissions must not fall back to unrelated news.
        if re.search(r'open\s*house', q, re.I):
            rows = [r for r in rows if re.search(r'open\s*house', r.title, re.I)]
        elif any(w in q for w in ['รับสมัคร', 'สมัครเรียน']):
            rows = [r for r in rows if 'รับสมัคร' in r.title + ' ' + (r.content or '')]
        english = re.findall(r'[a-zA-Z]{3,}', q.lower())
        if english and not event_rows:
            rows = [r for r in rows if all(w in (r.title + ' ' + (r.content or '')).lower() for w in english)]
        if any(w in q for w in ['ล่าสุด', 'ใหม่สุด', 'ใหม่ที่สุด']):
            dated = [(published_date(r.content), r) for r in rows]
            dated = [(d, r) for d, r in dated if d is not None and d <= date.today()]
            if not dated:
                return []
            newest = max(d for d, _ in dated)
            rows = [r for d, r in dated if d == newest]
            prefix = 'ข่าวที่มีวันที่เผยแพร่ล่าสุดในข้อมูลที่จัดเก็บและระบุวันที่เผยแพร่ ไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์ ไม่ใช้วันที่เพิ่มข้อมูลหรือวันที่จัดกิจกรรมแทนวันเผยแพร่:\n'
        else:
            prefix = 'ข่าวที่จัดเก็บในระบบ ไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์:\n'
        return [source(r.title, f'/records/news/{r.id}',
                       prefix + (r.content or '')[:4500]) for r in rows[:5]]
    return None
