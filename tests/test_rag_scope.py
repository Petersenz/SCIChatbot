import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from sqlalchemy import select,text
from backend.db import Session,Document
from backend.rag import retrieve,resolve_query
from backend.text_processing import extract_pdf,split_evidence

def test_plan_extraction():
 s=extract_pdf('data/uploads/adf8e969e3738ff9838e5116dbb13808.pdf')
 chunks=split_evidence(s)
 first=next(c for c in chunks if 'ปีที่ 1 / ภาคการศึกษาที่ 1' in c)
 assert 'SCCS1101' in first and 'รวม 18' in first
 assert 'SCCS1102' not in first
 assert '\uf70b' not in s

def test_scoped_retrieval():
 with Session() as db:
  db.execute(text('SET TRANSACTION READ ONLY'))
  for name in ['วิทยาการคอมพิวเตอร์','วิทย์คอม','CS']:
   sources=retrieve(db,f'{name} ปี 2570 ปี 1 เทอม 1 เรียนกี่หน่วยกิต')
   assert sources and all(s['document_id']==70 for s in sources)
   assert 'รวม 18' in sources[0]['text']
   assert 'ภาคการศึกษาที่ 2' not in sources[0]['text']
  assert retrieve(db,'วิทย์คอม ปี 2599 เทอมแรกเรียนอะไร')==[]
  q=resolve_query(db,'แล้วเทอม 2 ล่ะ',[SimpleNamespace(user_query='วิทยาการคอมพิวเตอร์ ปี 2570 ปี 1 เทอม 1 เรียนอะไร')])
  sources=retrieve(db,q)
  assert sources and 'SCCS1102' in sources[0]['text']
  assert 'SCCS1101' not in sources[0]['text']
  old=retrieve(db,'วิทยาการคอมพิวเตอร์ ปี 2564 รวมกี่หน่วยกิต')
  assert '128' in old[0]['text']
  assert len(retrieve(db,'คณะมีกี่สาขา'))==1


def test_exact_user_first_term_without_study_year():
 with Session() as db:
  db.execute(text('SET TRANSACTION READ ONLY'))
  sources=retrieve(db,'วิทย์คอม ปี 2570 เทอมแรกเรียนอะไรบ้าง')
  assert len(sources)==1 and sources[0]['document_id']==70
  evidence=sources[0]['text']
  assert 'ปีการศึกษา 2570' in evidence
  assert 'ปีที่ 1 / ภาคการศึกษาที่ 1' in evidence
  assert 'SCCS1101' in evidence and 'รวม 18' in evidence
  assert 'ปีที่ 3' not in evidence and 'SCCS3103' not in evidence
  followup=resolve_query(db,'แล้วเทอม 2 ล่ะ',[SimpleNamespace(user_query='วิทย์คอม ปี 2570 เทอมแรกเรียนอะไรบ้าง')])
  second=retrieve(db,followup)[0]['text']
  assert 'ปีที่ 1 / ภาคการศึกษาที่ 2' in second and 'SCCS1102' in second
  assert 'ปีที่ 2' not in second
  explicit=retrieve(db,'วิทย์คอม ปี 2570 ปี 3 เทอมแรกเรียนอะไรบ้าง')
  assert 'SCCS3103' in explicit[0]['text'] and 'SCCS1101' not in explicit[0]['text']
