from types import SimpleNamespace as N
from sqlalchemy import select
from backend.db import Session,MODELS
from backend.rag import retrieve,resolve_query
from backend.query_understanding import canonical

def test_total_credits_preserves_cohort_year_qualification():
 with Session() as db:
  result=retrieve(db,'วิทย์คอม ปี2570 หน่วยกิตรวมตลอดหลักสูตร')
  assert len(result)==1 and result[0]['url']=='/records/curricula/24'
  assert '121' in result[0]['text']
  assert 'ปีรับเข้า' in result[0]['text'] and 'ไม่ยืนยันว่าเป็นปีปรับปรุงหลักสูตร' in result[0]['text']

def test_quota_classifier_uses_installed_sdk_error_shape():
 from google.genai.errors import ClientError
 from backend.rag import quota_kind
 error=ClientError(429,{'error':{'details':[{'violations':[{'quotaId':'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}})
 assert quota_kind(error)=='daily'

def test_aliases_and_general_followup_do_not_inherit_semester():
 with Session() as db:
  for q in ['วิทคอม','Computer Science','คอมพิวเตอร์ไซเอนซ์','CS']:
   assert 'วิทยาการคอมพิวเตอร์' in canonical(q)
  q=resolve_query(db,'แล้วทุนล่ะ',[N(user_query='วิทย์คอม ปี 2570 ปี 1 เทอม 2')])
  assert 'วิทยาการคอมพิวเตอร์' in q and '2570' not in q and 'เทอม' not in q
  assert 'วิทยาการคอมพิวเตอร์' not in resolve_query(db,'ขอเบอร์ติดต่อของคณะ',[N(user_query='วิทย์คอมมีทุนไหม')])

def test_general_variations_are_scoped_and_unknown_year_is_not_invented():
 with Session() as db:
  for q,path in [('วิทคอมมีอาจารย์ใครบ้าง','/records/general/28'),('CS ก.ย.ศ. กู้ได้ไหม','/records/general/27'),('วิทย์คอมสมัครยังไง','/records/general/30'),('วิทย์คอมมีบริการอะไรให้นักศึกษาบ้าง','/records/general/29')]:
   result=retrieve(db,q)
   assert result and all(s['url']==path for s in result)
  assert retrieve(db,'วิทย์คอมมีทุนอะไรในปี 2599')==[]

def test_complete_career_section_does_not_leak_adjacent_personal_data():
 with Session() as db:
  result=retrieve(db,'วิทย์คอมหลักสูตร 2564 จบไปทำอะไรได้บ้าง')
  assert len(result)==1 and result[0]['url']=='/records/curricula/12'
  assert all('8.'+str(i) in result[0]['text'] for i in range(1,9))
  assert 'บัตรประชาชน' not in result[0]['text'] and '9.1' not in result[0]['text']
  assert retrieve(db,'วิทย์คอมหลักสูตร 2599 จบไปทำอะไรได้บ้าง')==[]
