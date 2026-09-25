from datetime import date
from types import SimpleNamespace as N
from backend.structured_evidence import published_date,retrieve_managed

def test_explicit_numeric_publication_date_only():
 assert published_date('โพสต์เมื่อ 26/08/2569')==date(2026,8,26)
 assert published_date('กิจกรรมวันที่ 26/08/2569') is None
 assert published_date('โพสต์เมื่อ 31/02/2569') is None

def test_major_topic_does_not_mix_other_major():
 class Result:
  def __init__(self,rows):self.rows=rows
  def __iter__(self):return iter(self.rows)
  def all(self):return self.rows
 class DB:
  count=0
  def scalars(self,q):
   self.count+=1
   return Result([] if self.count==1 else [N(id=1,topic='วิทยาการคอมพิวเตอร์: ทุนการศึกษา',description='ทุนCS'),N(id=2,topic='เคมี: ทุนการศึกษา',description='ทุนเคมี')])
 sources=retrieve_managed(DB(),'วิทยาการคอมพิวเตอร์มีทุนอะไรบ้าง',[N(id=12,major_name_th='วิทยาการคอมพิวเตอร์')],[])
 assert len(sources)==1 and sources[0]['url']=='/records/general/1'
