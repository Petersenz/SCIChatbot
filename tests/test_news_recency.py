from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as N
import pytest
from sqlalchemy import create_engine, BigInteger
from sqlalchemy.orm import Session
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from backend.db import Base, MODELS, CurriculumCareer
from backend import rag
from backend.news_recency import added_news, recency_mode

@compiles(JSONB,'sqlite')
def jsonb(type,compiler,**kw):return 'JSON'
@compiles(BigInteger,'sqlite')
def bigint(type,compiler,**kw):return 'INTEGER'

@pytest.fixture
def db(monkeypatch):
 engine=create_engine('sqlite://')
 Base.metadata.create_all(engine,tables=[m.__table__ for m in MODELS.values()]+[CurriculumCareer.__table__])
 with Session(engine) as session:
  session.add(MODELS['majors'](id=1,major_name_th='วิทยาการคอมพิวเตอร์'))
  session.add(MODELS['majors'](id=2,major_name_th='เทคโนโลยีสารสนเทศ'))
  session.add_all([
   MODELS['news'](id=10,title='Old Conference วิทยาการคอมพิวเตอร์',content='เผยแพร่เมื่อ 15 กันยายน 2569',created_at=datetime(2026,9,23,tzinfo=timezone.utc)),
   MODELS['news'](id=11,title='New Student Award',content='นักศึกษาเทคโนโลยีสารสนเทศได้รับรางวัล',created_at=datetime(2026,9,27,tzinfo=timezone.utc)),
   MODELS['news'](id=99,title='Imported Old Event วิทยาการคอมพิวเตอร์',content='จัดวันที่ 30 กันยายน 2569',created_at=datetime(2026,9,20,tzinfo=timezone.utc)),
  ]);session.commit()
  def forbidden(*args,**kwargs):raise AssertionError('No LLM or embeddings for managed latest headline')
  monkeypatch.setattr(rag,'generate_with_retry',forbidden)
  monkeypatch.setattr(rag,'embed',forbidden)
  yield session
 engine.dispose()

def retrieve(db,q,h=()):
 query=rag.resolve_query(db,q,h)
 return rag.retrieve(db,query)

@pytest.mark.parametrize('q',['ข่าวล่าสุดคือข่าวอะไร','ข่าวใหม่สุดของคณะ','ข่าวใหม่ที่สุด','มีข่าวอะไรล่าสุด','ข่าวที่เพิ่งเพิ่มคืออะไร'])
def test_default_new_record_without_publication_date(db,q):
 body,sources,answered,_,mode=rag.answer(db,q,[])
 assert [s['url'] for s in sources]==['/records/news/11']
 assert answered and mode=='grounded'
 assert 'New Student Award' in body and '27/09/2569' in body
 assert 'วันที่เพิ่มข้อมูล' in body

def test_explicit_publication_order(db):
 assert [s['url'] for s in retrieve(db,'ข่าวที่เผยแพร่ล่าสุดคืออะไร')]==['/records/news/10']

def test_major_filter_precedes_order(db):
 assert [s['url'] for s in retrieve(db,'ข่าวล่าสุดวิทย์คอมคืออะไร')]==['/records/news/10']

def test_event_followup_then_latest_starts_new_news_lookup(db):
 history=[N(user_query='Old Conference คืออะไร',sources=[{'url':'/records/news/10'}])]
 assert [s['url'] for s in retrieve(db,'แล้วข่าวล่าสุดล่ะ',history)]==['/records/news/11']

def test_selected_latest_followup_retains_record(db):
 history=[N(user_query='ข่าวล่าสุดคือข่าวอะไร',sources=[{'url':'/records/news/11'}])]
 assert [s['url'] for s in retrieve(db,'ข่าวนี้มีใครบ้าง',history)]==['/records/news/11']

def test_insert_edit_delete_visible_without_vector_or_generation_cache(db):
 assert '/news/11' in retrieve(db,'ข่าวล่าสุดคืออะไร')[0]['url']
 row=MODELS['news'](id=12,title='Newest Managed Item',content='เนื้อหาใหม่',created_at=datetime(2026,9,28,tzinfo=timezone.utc))
 db.add(row);db.commit()
 assert 'Newest Managed Item' in rag.answer(db,'ข่าวล่าสุดคืออะไร',[])[0]
 row.title='Changed Managed Title';row.content='แก้ไขรายละเอียด';db.commit()
 assert 'Changed Managed Title' in rag.answer(db,'ข่าวล่าสุดคืออะไร',[])[0]
 db.delete(row);db.commit()
 assert '/news/11' in retrieve(db,'ข่าวล่าสุดคืออะไร')[0]['url']

def test_stable_ties_and_missing_dates():
 stamp=datetime(2026,9,27,tzinfo=timezone.utc)
 assert added_news([N(id=1,created_at=stamp),N(id=2,created_at=stamp)])[0].id==2
 assert added_news([N(id=3,created_at=None)])==[]
 # Naive UTC and aware timezone values refer to the same instant.
 assert added_news([N(id=1,created_at=stamp.replace(tzinfo=None)),N(id=2,created_at=stamp.astimezone(timezone(timedelta(hours=7))))])[0].id==2

def test_empty_scope_does_not_fallback(db):
 assert retrieve(db,'ข่าวล่าสุดสาขาเทคโนโลยีสารสนเทศปี 2599')==[]
