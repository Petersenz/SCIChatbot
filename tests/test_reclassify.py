import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from backend.db import Base,MODELS,Document,Chunk,Chat,Conversation
from backend.reclassify import apply,validate
from backend.reclassify_backup import capture,restore,restore_values
from backend.conversation_plan import Catalog,make_plan
from backend.structured_evidence import retrieve_managed
@compiles(JSONB,'sqlite')
def json_sqlite(type,compiler,**kw):return 'JSON'

@pytest.fixture
def migrated_data():
 root=Path('/home/ubuntu/sci-chatbot-staging/20260925')
 if not (root/'migration-plan.json').exists():pytest.skip('Reviewed snapshot is kept outside repository')
 data=json.loads((root/'before.json').read_text(encoding='utf-8-sig'));plan=json.loads((root/'migration-plan.json').read_text(encoding='utf-8-sig'))
 engine=create_engine('sqlite://');Base.metadata.create_all(engine)
 with Session(engine) as db:
  for table,rows in data.items():
   for row in rows:db.add(MODELS[table](**restore_values(MODELS[table],row)))
  db.add(Conversation(id='fixture'));db.flush()
  db.add(Chat(id=1,session_id='fixture',user_query='test',bot_response='answer [1]',sources=[{'title':'old','url':'/records/general/28'}]))
  for item in plan['retire']:
   d=Document(url='/records/general/'+str(item['id']),record_type='general',record_id=item['id'],content='stale',title='old');db.add(d);db.flush();db.add(Chunk(document_id=d.id,content='stale',embedding=[0.0]*768))
  db.commit()
  # SQLite discards timezone offsets, unlike the production PostgreSQL types.
  for item in plan['retire']:
   row=db.get(MODELS[item['table']],item['id'])
   for key in ('created_at','updated_at'):item['before'][key]=str(getattr(row,key))
  yield db,plan
 engine.dispose()

def sync_stub(table,row,db):
 d=db.scalar(select(Document).where(Document.record_type==table,Document.record_id==row.id))
 if not d:d=Document(url=f'/records/{table}/{row.id}',record_type=table,record_id=row.id);db.add(d)
 d.content=row.description;d.title=getattr(row,'topic',None) or getattr(row,'major_name_th',None) or row.degree_name

def test_atomic_move_index_citations_and_restore(migrated_data):
 db,plan=migrated_data;before=capture(db,plan);apply(db,plan,sync_stub);db.commit()
 assert all(db.get(MODELS['general'],i) is None for i in [25,26,28])
 assert db.scalar(select(Chat)).sources[0]['url']=='/records/majors/12'
 assert not list(db.scalars(select(Chunk)))
 assert 'ส่วนกลาง' in db.get(MODELS['general'],27).topic
 assert db.get(MODELS['curricula'],24).curriculum_year==2570
 restore(db,before);db.commit()
 assert all(db.get(MODELS['general'],i) for i in [25,26,28])
 assert db.scalar(select(Chat)).sources[0]['url']=='/records/general/28'
 assert len(list(db.scalars(select(Chunk))))==3
 assert db.get(MODELS['majors'],12).description==next(x['values']['description'] for x in before['records'] if x['table']=='majors')

def test_precondition_and_failure_rollback(migrated_data):
 db,plan=migrated_data
 db.get(MODELS['general'],27).topic='concurrent edit'
 with pytest.raises(ValueError):validate(db,plan)
 db.rollback()
 def fail(*args):raise RuntimeError('index failed')
 with pytest.raises(RuntimeError):apply(db,plan,fail)
 db.rollback();validate(db,plan)

@pytest.mark.parametrize('q,expected',[('อาจารย์วิทย์คอมมีใครบ้าง','/records/majors/12'),('ติดต่อวิทย์คอม','/records/majors/12'),('วิทย์คอมมีบริการนักศึกษาอะไรบ้าง','/records/general/29'),('วิทย์คอมมีทุนอะไรบ้าง','/records/general/27'),('ขอเบอร์ติดต่อคณะ','/records/general/1')])
def test_actual_data_retrieval_after_move(migrated_data,q,expected):
 db,plan=migrated_data;apply(db,plan,sync_stub)
 catalog=Catalog.load(db);p=make_plan(q,[],catalog)
 sources=retrieve_managed(db,p.query,catalog.majors,list(db.scalars(select(MODELS['curricula']))),p)
 assert sources and sources[0]['url']==expected
