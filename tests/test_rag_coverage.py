"""Coverage of thesis 1.3.1 question categories; not a research accuracy score."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
import pytest
from sqlalchemy import select,text
from backend.db import Session,MODELS
from backend.query_understanding import canonical,resolve,ambiguity,topic
from backend.rag import retrieve,answer

@pytest.fixture
def db():
 with Session() as d:
  d.execute(text('SET TRANSACTION READ ONLY'))
  yield d

@pytest.mark.parametrize('q',[
 'วิทย์คอม ปี 2570 ปี 1 เทอม 2 เรียนอะไร',
 'วิทย์คอม ปี ๒๕๗๐ ปี ๑ เทอม ๒ เรียนอะไร',
 'CS ปี 2027 ปีหนึ่ง เทอมสองเรียนอะไร',
 'วิทยาการคอมพิวเตอร์ ปี 2570 ปีที่หนึ่ง ภาคเรียนที่สองเรียนอะไร',
 'วิทย์คอม ปี 2570 ปี 1 ภาคการศึกษา ที่ 2 เรียนอะไร',
])
def test_semester_variants(db,q):
 s=retrieve(db,q)
 assert s and all(x['document_id']==70 for x in s)
 assert 'SCCS1102' in s[0]['text'] and 'SCCS1101' not in s[0]['text']

@pytest.mark.parametrize('q',[
 'วิทย์คอม ปี 2570 ค่าเทอม 1 เท่าไหร่',
 'วิทย์คอม ปี 2570 ค่าเล่าเรียนเท่าไหร่',
 'CS ปี 2570 ค่าธรรมเนียมการศึกษาต่อเทอม',
])
def test_tuition_not_course_table(db,q):
 s=retrieve(db,q)
 assert len(s)==1 and s[0]['url']=='/records/curricula/24'
 assert '8000' in s[0]['text'] and 'SCCS' not in s[0]['text']

@pytest.mark.parametrize('q', ['คณะมีสาขาอะไรบ้าง','คณะเปิดสอนหลักสูตรอะไรบ้าง','มีกี่สาขา'])
def test_overview(db,q):
 assert '12 รายการ' in retrieve(db,q)[0]['text']

@pytest.mark.parametrize('q,word',[('คณะตั้งอยู่ที่ไหน','สะเดียง'),('คณะก่อตั้งเมื่อไหร่','2518'),('คณะมีวิสัยทัศน์อะไร','วิสัยทัศน์')])
def test_general(db,q,word):
 s=retrieve(db,q)
 assert s and word in s[0]['text']
 assert all('/records/general/' in x['url'] for x in s)

def test_news_specific(db):
 s=retrieve(db,'ข่าว Open House 2569 มีรายละเอียดอะไร')
 assert s and all('Open House' in x['title'] for x in s)
 assert all('/records/news/' in x['url'] for x in retrieve(db,'คณะมีข่าวอะไรบ้าง'))
 assert retrieve(db,'ข่าว Open House 2599 มีอะไรบ้าง')==[]
 assert retrieve(db,'วิทย์คอม รับสมัครปี 2599 ถึงวันไหน')==[]

def test_careers(db):
 s=retrieve(db,'วิทย์คอมจบไปทำงานอะไรได้บ้าง')
 assert s and all('/records/careers/' in x['url'] for x in s)
 assert any('Flutter' in x['text'] for x in s)
 assert any('15000' in x['text'] for x in s)
 assert len({x['url'] for x in s})==len(s)

def test_named_curriculum_not_faculty_overview(db):
 s=retrieve(db,'วิทย์คอมมีหลักสูตรอะไร')
 assert s and all('วิทยาการคอมพิวเตอร์' in x['title'] for x in s)

def test_alias_it_and_switch(db):
 majors=list(db.scalars(select(MODELS['majors'])))
 history=[SimpleNamespace(user_query='วิทย์คอม ปี 2570 เทอมแรกเรียนอะไร')]
 q=resolve('แล้ว IT เรียนอะไร',history,majors)
 assert 'วิทยาการคอมพิวเตอร์' not in q and '2570' not in q
 assert 'เทคโนโลยีสารสนเทศ' in q
 s=retrieve(db,q)
 assert s and all('เทคโนโลยีสารสนเทศ' in x['title'] for x in s)

def test_multiturn(db):
 majors=list(db.scalars(select(MODELS['majors'])))
 history=[SimpleNamespace(user_query=x) for x in ['วิทย์คอม ปี 2570 เทอมแรกเรียนอะไร','แล้วเทอม 2 ล่ะ']]
 q=resolve('กี่หน่วยกิต',history,majors)
 assert '2570' in q and 'ปีที่ 1' in q and 'เทอม 2' in q
 assert 'SCCS1102' in retrieve(db,q)[0]['text']
 q=resolve('วิทย์คอม ปี 2564 รวมกี่หน่วยกิต',history,majors)
 assert 'ปีที่ 1' not in q and 'เทอม 2' not in q
 assert '128' in retrieve(db,q)[0]['text']

@pytest.mark.parametrize('q',['ชีววิทยามีหลักสูตรอะไร','คณิตศาสตร์เรียนอะไร','วิทย์คอมเทียบกับไอทีเรียนต่างกันยังไง','วิทย์คอม ปี 2570 เทอม 2 เรียนอะไร','วิทย์คอม ปี 2564 กับ 2570 ต่างกันไหม','วิทย์คอม ปี 2570 ปี 1 เทอม 1 และเทอม 2 เรียนอะไร'])
def test_clarify_ambiguity(db,q):
 body,sources,ok,_,mode=answer(db,q,[])
 assert mode=='clarification' and not ok and sources==[]
 assert 'ไหน' in body

@pytest.mark.parametrize('q',['วิทย์คอม ปี 2570 ปี 1 เทอม 3 เรียนอะไร','วิทย์คอม ปี 2599 เทอมแรกเรียนอะไร','วิทย์คอม ปี 2570 SCCS9999 คือวิชาอะไร'])
def test_no_wrong_substitution(db,q):
 assert retrieve(db,q)==[]

def test_course_code(db):
 s=retrieve(db,'วิทย์คอม ปี 2570 SCCS1102 คือวิชาอะไร')
 assert s and all('SCCS1102' in x['text'] for x in s)

def test_greeting(db):
 assert answer(db,'สวัสดีครับ',[])[-1]=='rule_based'

@pytest.mark.parametrize('name', ['ชีววิทยา วิชาเอกจุลชีววิทยา','คณิตศาสตร์และวิทยาการคำนวณ','การแพทย์แผนไทย','สาธารณสุขศาสตร์','เทคโนโลยีอาหารและการพัฒนาผลิตภัณฑ์','การจัดการทรัพยากรธรรมชาติและสิ่งแวดล้อม','คณิตศาสตร์และสถิติประยุกต์','ชีววิทยา วิชาเอกชีววิทยา','เคมี','ฟิสิกส์ประยุกต์','เทคโนโลยีสารสนเทศ','วิทยาการคอมพิวเตอร์'])
def test_full_major_identity(db,name):
 majors=list(db.scalars(select(MODELS['majors'])))
 assert ambiguity(name+' เรียนอะไร',majors) is None
 assert name in resolve(name+' เรียนอะไร',[],majors)
