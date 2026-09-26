from types import SimpleNamespace as N
import pytest
from backend.conversation_plan import Catalog, Entity, make_plan, choose_intent, PUBLIC_TABLES


@pytest.fixture
def catalog():
    majors = [N(id=1, major_name_th='วิทยาการคอมพิวเตอร์'), N(id=2, major_name_th='เทคโนโลยีสารสนเทศ')]
    entities = [
        Entity('general', 11, 'วิทยาการคอมพิวเตอร์: ทุนการศึกษา'),
        Entity('general', 12, 'วิทยาการคอมพิวเตอร์: บุคลากร'),
        Entity('general', 13, 'วิทยาการคอมพิวเตอร์: วิธีสมัคร'),
        Entity('general', 14, 'วิทยาการคอมพิวเตอร์: บริการนักศึกษา'),
        Entity('general', 15, 'ติดต่อคณะวิทยาศาสตร์และเทคโนโลยี'),
        Entity('general', 16, 'ประวัติคณะวิทยาศาสตร์และเทคโนโลยี'),
        Entity('general', 17, 'วิสัยทัศน์และพันธกิจ'),
        Entity('news', 21, 'Future Lab 2571 กิจกรรมต้อนรับนักศึกษา'),
        Entity('news', 22, 'Future Lab 2572 กิจกรรมต้อนรับนักศึกษา'),
        Entity('careers', 31, 'นักพัฒนาเว็บและโมบายด์แอปพลิเคชัน'),
    ]
    return Catalog(majors, entities, [])


def plan(catalog, q, history=()):
    return make_plan(q, [N(user_query=x) if isinstance(x, str) else x for x in history], catalog)


@pytest.mark.parametrize('first,follow,route,record', [
    ('วิทย์คอมมีทุนอะไรบ้าง', 'ทุนนี้ต้องใช้เอกสารอะไร', 'scholarship', 11),
    ('วิทย์คอมมีอาจารย์ใครบ้าง', 'ขอรายละเอียดเพิ่มเติม', 'staff', 12),
    ('วิทย์คอมสมัครยังไง', 'ต้องใช้เอกสารอะไรบ้าง', 'admissions', 13),
    ('วิทย์คอมมีบริการนักศึกษาอะไรบ้าง', 'ขอรายละเอียดเพิ่มเติม', 'services', 14),
    ('ขอเบอร์ติดต่อของคณะ', 'แล้วอีเมลล่ะ', 'contact', 15),
    ('ประวัติคณะเป็นอย่างไร', 'ขอรายละเอียดเพิ่มเติม', 'history', 16),
    ('คณะมีวิสัยทัศน์อะไร', 'ขอรายละเอียดเพิ่มเติม', 'mission', 17),
    ('Future Lab 2571 คืออะไร', 'จัดที่ไหน', 'news', 21),
    ('Future Lab 2571 คืออะไร', 'จัดวันไหน', 'news', 21),
    ('วิทย์คอมจบไปทำเว็บได้ไหม', 'เงินเดือนประมาณเท่าไหร่', 'career', 31),
])
def test_shared_entity_followups(catalog, first, follow, route, record):
    result = plan(catalog, follow, [first])
    assert result.route == route
    assert [e.id for e in result.entities] == [record]
    assert result.clarification is None
    assert set(result.allowed_tables) <= set(PUBLIC_TABLES)


def test_switch_and_return_reuses_topic_frame(catalog):
    result = plan(catalog, 'กลับไปเรื่องทุน ต้องใช้เอกสารอะไร', ['วิทย์คอมมีทุนไหม', 'Future Lab 2571 คืออะไร'])
    assert result.transition == 'return' and result.entities[0].id == 11
    assert 'Future Lab' not in result.query and '2571' not in result.query


def test_new_major_cannot_keep_previous_general_record(catalog):
    result = plan(catalog, 'แล้วไอทีมีทุนไหม', ['วิทย์คอมมีทุนไหม'])
    assert not result.entities and 'วิทยาการคอมพิวเตอร์' not in result.query


def test_unknown_reference_needs_clarification(catalog):
    result = plan(catalog, 'อันที่สองมีรายละเอียดอะไร')
    assert result.clarification and not result.entities


def test_ordinal_uses_current_session_source_identities(catalog):
    previous = N(user_query='มีข่าวกิจกรรมอะไรบ้าง', sources=[{'url': '/records/news/21'}, {'url': '/records/news/22'}])
    result = plan(catalog, 'ข่าวที่สองจัดที่ไหน', [previous])
    assert [e.id for e in result.entities] == [22]
    assert not result.clarification
    assert plan(catalog, 'ข่าวที่สองจัดที่ไหน').clarification


def test_deleted_or_private_reference_cannot_be_selected(catalog):
    previous = N(user_query='มีข่าวอะไร', sources=[{'url': '/records/users/1'}, {'url': '/records/news/999'}])
    result = plan(catalog, 'ข่าวแรกจัดที่ไหน', [previous])
    assert result.clarification and not result.entities


def test_new_database_title_requires_no_code_change(catalog):
    catalog.entities.append(Entity('news', 77, 'Quantum Camp 2573 เปิดบ้าน'))
    result = plan(catalog, 'จัดวันไหน', ['Quantum Camp 2573 คืออะไร'])
    assert [e.id for e in result.entities] == [77]


def test_unknown_input_does_not_search_all_records(catalog):
    assert plan(catalog, '2+3 เท่ากับเท่าไหร่', ['วิทย์คอมมีทุนไหม']).clarification


def test_intent_match_must_be_positive_unique_and_active():
    def intent(id, context, **kwargs):
        return N(id=id, intent_name='รายการ'+str(id), prompt_context=context, action_type=kwargs.get('action', 'rag'), static_response='สวัสดีค่ะ', is_active=kwargs.get('active', True))
    intents = [intent(1, 'ทุน,กยศ'), intent(2, 'เงินเดือน'), intent(3, 'สวัสดี', action='rule_based'), intent(4, 'ข่าว', active=False)]
    assert choose_intent('มีทุนไหม', intents).id == 1
    assert choose_intent('สวัสดีครับ', intents).id == 3
    assert choose_intent('สวัสดีครับ เงินเดือนเท่าไหร่', intents).id == 2
    assert choose_intent('ข่าวอะไร', intents) is None
    assert choose_intent('ไม่ตรงหมวด', intents) is None
    assert choose_intent('มีทุนไหม', [intents[0], intent(5, 'ทุน,กยศ')]) is None


def test_mutable_intent_configuration_is_not_cached(catalog):
    row = N(id=3, intent_name='ทุน', prompt_context='ทุน', action_type='rag', static_response=None, is_active=True)
    catalog.intents.append(row)
    assert plan(catalog, 'มีทุนไหม').intent_id == 3
    row.is_active = False
    assert plan(catalog, 'มีทุนไหม').intent_id is None


def test_year_semester_and_tuition_remain_separate(catalog):
    result = plan(catalog, 'ทั้งหลักสูตรมีกี่หน่วยกิต', ['วิทย์คอม ปี 2570 เทอมแรกเรียนอะไร', 'แล้วเทอมสองล่ะ'])
    assert result.year == '2570' and result.term is None and result.study_year is None
    result = plan(catalog, 'ค่าเทอมเท่าไหร่', ['วิทย์คอม ปี 2570 เทอมแรกเรียนอะไร'])
    assert result.route == 'tuition' and result.year == '2570'
    assert result.requested_fields == ('tuition_fee',)


def test_event_year_changes_do_not_mix_prior_year(catalog):
    result = plan(catalog, 'แล้วปี 2572 จัดวันไหน', ['Future Lab 2571 คืออะไร'])
    assert [e.id for e in result.entities] == [22]
    assert '2571' not in result.query and '2572' in result.query
