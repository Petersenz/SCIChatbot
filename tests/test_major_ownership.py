from types import SimpleNamespace as N
import pytest
from backend.major_sections import section,owned_sources
from backend.conversation_plan import Catalog,Entity,make_plan

def cat():
 return Catalog([N(id=1,major_name_th='วิทยาการคอมพิวเตอร์',description='ภาพรวม\n## บุคลากร\nอาจารย์ทดสอบ\n## ติดต่อ\nอาคาร A',tel='056111111',email='cs@example.test'),N(id=2,major_name_th='เทคโนโลยีสารสนเทศ',description='ภาพรวม',tel='',email='')],[Entity('general',7,'ทุนการศึกษา (ข้อมูลส่วนกลาง)'),Entity('general',9,'บริการนักศึกษา (ส่วนกลางมหาวิทยาลัย)'),Entity('general',4,'ติดต่อคณะ'),Entity('general',5,'เทคโนโลยีสารสนเทศ: บุคลากร')],[])

def test_section_is_bounded_and_duplicate_fails_closed():
 assert section(cat().majors[0].description,'บุคลากร')=='อาจารย์ทดสอบ'
 assert not section('## บุคลากร\nA\n## บุคลากร\nB','บุคลากร')

@pytest.mark.parametrize('q,route,record',[('วิทย์คอมมีบริการนักศึกษาอะไรบ้าง','services',9),('วิทย์คอมมีทุนอะไรบ้าง','scholarship',7),('บริการนักศึกษามีอะไรบ้าง','services',9),('ทุนการศึกษามีอะไรบ้าง','scholarship',7)])
def test_explicit_common_information_available(q,route,record):
 p=make_plan(q,[],cat());assert p.route==route and p.entities[0].id==record and not p.clarification

def test_specific_request_not_replaced_by_common():
 p=make_plan('ทุนเฉพาะสาขาวิทยาการคอมพิวเตอร์',[],cat());assert not p.entities

def test_roster_from_major_and_followup():
 c=cat();p=make_plan('ขอรายละเอียดเพิ่มเติม',[N(user_query='อาจารย์วิทย์คอมมีใครบ้าง')],c)
 s=owned_sources(p,c.majors);assert s[0]['url']=='/records/majors/1' and 'อาจารย์ทดสอบ' in s[0]['text'] and 'อาคาร' not in s[0]['text']

def test_contact_preserves_address_but_not_roster():
 c=cat();p=make_plan('ติดต่อวิทย์คอม',[],c);s=owned_sources(p,c.majors)[0]
 assert '056111111' in s['text'] and 'อาคาร A' in s['text'] and 'อาจารย์ทดสอบ' not in s['text']

def test_major_switch_never_uses_other_roster():
 c=cat();p=make_plan('แล้วไอทีมีอาจารย์ใครบ้าง',[N(user_query='อาจารย์วิทย์คอมมีใครบ้าง')],c)
 assert owned_sources(p,c.majors) is None and all(e.id!=1 for e in p.entities)

def test_existing_scoped_topic_beats_common():
 c=cat();c.entities.append(Entity('general',20,'วิทยาการคอมพิวเตอร์: ทุนการศึกษา'))
 assert make_plan('วิทย์คอมมีทุนไหม',[],c).entities[0].id==20


def test_exclusive_followup_cannot_reuse_common_source():
 p=make_plan("ทุนเฉพาะวิทย์คอมมีอะไรบ้าง",[N(user_query="วิทย์คอมมีทุนอะไรบ้าง")],cat())
 assert not p.entities
