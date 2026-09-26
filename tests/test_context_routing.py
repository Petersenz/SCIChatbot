"""Scope isolation regressions; synthetic data never touches the live DB."""
from types import SimpleNamespace as N
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.db import MODELS, User, CurriculumCareer
from backend.query_understanding import resolve, ambiguity
from backend.structured_evidence import retrieve_managed
from backend.career_scope import career_answer

MAJORS = [N(id=1, major_name_th='วิทยาการคอมพิวเตอร์'), N(id=2, major_name_th='เทคโนโลยีสารสนเทศ')]
TITLES = ['นักพัฒนาเว็บและโมบายด์แอปพลิเคชัน', 'สถาปนิกฐานข้อมูล (Database Architect)']


def resolved(q, history=()):
    return resolve(q, [N(user_query=x) for x in history], MAJORS, TITLES)


@pytest.mark.parametrize('q', ['เงินเดือนประมาณเท่าไหร่', 'รายได้ประมาณเท่าไหร่', 'ต้องมีทักษะอะไรบ้าง'])
def test_major_and_job_followups(q):
    value = resolved(q, ['คณะมีสาขาอะไรบ้าง', '2+3 เท่ากับเท่าไหร่', 'วิทยาการคอมพิวเตอร์ จบไปทำเว็บได้ไหม'])
    assert MAJORS[0].major_name_th in value and TITLES[0] in value


def test_acknowledgements_and_no_cross_session():
    assert TITLES[0] in resolved('เงินเดือนเท่าไหร่', ['วิทย์คอมจบไปทำเว็บได้ไหม', 'ขอบคุณครับ'])
    assert ambiguity(resolved('เงินเดือนเท่าไหร่'), MAJORS, TITLES)


def test_major_switch_clears_job_and_old_year():
    value = resolved('แล้วไอทีเงินเดือนเท่าไหร่', ['วิทย์คอม ปี 2570 จบไปทำเว็บได้ไหม'])
    assert MAJORS[1].major_name_th in value
    assert MAJORS[0].major_name_th not in value and TITLES[0] not in value and '2570' not in value


def test_ambiguous_prior_major_is_not_silently_selected():
    value = resolved('เงินเดือนเท่าไหร่', ['วิทย์คอมกับไอทีจบไปทำงานอะไร'])
    assert ambiguity(value, MAJORS, TITLES)


def test_job_switch_and_explicit_all_jobs():
    history = ['วิทย์คอมจบไปทำเว็บได้ไหม']
    assert TITLES[0] not in resolved('สถาปนิกฐานข้อมูลเงินเดือนเท่าไหร่', history)
    assert TITLES[0] not in resolved('เงินเดือนทุกอาชีพเท่าไหร่', history)


def test_contact_and_news_do_not_inherit_web_job():
    history = ['วิทย์คอมจบไปทำเว็บได้ไหม']
    assert MAJORS[0].major_name_th not in resolved('ขอเบอร์ติดต่อของคณะ', history)
    assert TITLES[0] not in resolved('คณะมีข่าวอะไรบ้าง', history)


@pytest.fixture
def db():
    engine = create_engine('sqlite://')
    # Create only relational fixtures, excluding PostgreSQL vector/JSONB tables.
    tables = [User.__table__] + [MODELS[k].__table__ for k in ['majors', 'careers', 'curricula', 'news', 'general', 'intents']]
    User.metadata.create_all(engine, tables=tables + [CurriculumCareer.__table__])
    with Session(engine) as db:
        db.add_all([MODELS['majors'](id=m.id, major_name_th=m.major_name_th) for m in MAJORS])
        db.add_all([MODELS['curricula'](id=10, major_id=1, degree_name='CS', curriculum_year=2564), MODELS['curricula'](id=20, major_id=2, degree_name='IT', curriculum_year=2564)])
        db.add_all([MODELS['careers'](id=1, job_title=TITLES[0], salary_start=15000, skill_required='React'), MODELS['careers'](id=2, job_title='งานเฉพาะไอที', salary_start=99999), MODELS['careers'](id=3, job_title=TITLES[1], salary_start=50000, job_description='ระดับประสบการณ์ที่ใช้อ้างอิง: 3–5 ปี\nวิธีประมาณ: เทียบตำแหน่งใกล้เคียง\nไม่ควรใช้เป็นอัตราเริ่มต้นสำหรับผู้จบใหม่')])
        db.add_all([CurriculumCareer(curriculum_id=10, career_id=1), CurriculumCareer(curriculum_id=20, career_id=2)])
        db.flush()
        yield db
    engine.dispose()


def retrieve(db, q):
    from sqlalchemy import select
    return retrieve_managed(db, q, list(db.scalars(select(MODELS['majors']))), list(db.scalars(select(MODELS['curricula']))))


def test_foreign_and_unlinked_jobs_cannot_enter_scoped_answer(db):
    sources = retrieve(db, 'วิทยาการคอมพิวเตอร์เงินเดือนเท่าไหร่')
    assert [s['url'] for s in sources] == ['/records/careers/1']
    body, supported = career_answer('เงินเดือนเท่าไหร่', sources)
    assert supported and '15,000' in body and 'วิทยาการคอมพิวเตอร์' in body
    assert '99,999' not in body and '50,000' not in body


def test_missing_link_never_delegates_to_global_vector_search(db):
    assert retrieve(db, 'วิทยาการคอมพิวเตอร์สถาปนิกฐานข้อมูลเงินเดือนเท่าไหร่') == []
    assert retrieve(db, 'วิทยาการคอมพิวเตอร์ปี2599เงินเดือนเท่าไหร่') == []


def test_explicit_role_is_exact_and_keeps_experience(db):
    sources = retrieve(db, 'สถาปนิกฐานข้อมูลเงินเดือนเท่าไหร่')
    assert [s['url'] for s in sources] == ['/records/careers/3']
    body, supported = career_answer('เงินเดือนเท่าไหร่', sources)
    assert supported and '50,000' in body and '3–5 ปี' in body and 'เทียบตำแหน่งใกล้เคียง' in body
    body, supported = career_answer('เงินเดือนจบใหม่เท่าไหร่', sources)
    assert not supported and '50,000' not in body


def test_skill_answer_reads_current_fields(db):
    sources = retrieve(db, 'วิทยาการคอมพิวเตอร์ทักษะทำเว็บ')
    assert 'React' in career_answer('ทักษะอะไร', sources)[0]
    db.get(MODELS['careers'], 1).skill_required = 'Updated skill'
    db.flush()
    assert 'Updated skill' in career_answer('ทักษะอะไร', retrieve(db, 'วิทยาการคอมพิวเตอร์ทักษะทำเว็บ'))[0]


def test_similar_news_title_cannot_override_salary_route(db):
    db.add(MODELS['news'](id=1, title='เทคโนโลยีสารสนเทศ เปิดบ้าน', content='ข่าวกิจกรรม'))
    db.flush()
    sources = retrieve(db, 'เทคโนโลยีสารสนเทศเงินเดือนเท่าไหร่')
    assert [s['url'] for s in sources] == ['/records/careers/2']


def test_unresolved_ordinal_does_not_pick_arbitrary_career():
    q = resolved('อาชีพแรกเงินเดือนเท่าไหร่', ['วิทย์คอมจบไปทำงานอะไรได้บ้าง'])
    assert ambiguity(q, MAJORS, TITLES)


def test_held_out_salary_paraphrase_and_multiple_acknowledgements():
    q = resolved('ค่าตอบแทนต่อเดือนประมาณไหนครับ', ['Computer Science จบไปทำเว็บได้ไหม', 'โอเค', 'ขอบคุณค่ะ'])
    assert MAJORS[0].major_name_th in q and TITLES[0] in q


@pytest.mark.parametrize('provider', ['gemini', 'groq'])
def test_end_to_end_answer_never_calls_llm_or_embedding_for_salary(db, monkeypatch, provider):
    from backend import rag
    monkeypatch.setenv('LLM_PROVIDER', provider)
    def forbidden(*args, **kwargs):
        raise AssertionError('Structured salary must not call embedding/generation')
    monkeypatch.setattr(rag, 'embed', forbidden)
    monkeypatch.setattr(rag, 'generate_with_retry', forbidden)
    body, sources, supported, _, mode = rag.answer(db, 'เงินเดือนประมาณเท่าไหร่', [N(user_query='วิทย์คอมจบไปทำเว็บได้ไหม')])
    assert supported and mode == 'grounded' and '15,000' in body
    assert MAJORS[0].major_name_th in body and len(sources) == 1
    assert 'career_fact' not in sources[0]
    db.get(MODELS['careers'], 1).salary_start = 18000
    db.flush()
    assert '18,000' in rag.answer(db, 'เงินเดือนประมาณเท่าไหร่', [N(user_query='วิทย์คอมจบไปทำเว็บได้ไหม')])[0]
