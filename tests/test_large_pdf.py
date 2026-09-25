import io,time,json
from pathlib import Path
import pytest
from pypdf import PdfWriter
from pypdf.generic import NameObject,DecodedStreamObject,DictionaryObject
from sqlalchemy import select,func
from test_api import staff
from backend.db import ROOT,Session,Document,Chunk,MODELS
from backend.text_processing import extract_pdf,PDFValidationError,split_evidence
from backend.rag import retrieve


def pdf_fixture(pages,padded=False):
 writer=PdfWriter()
 font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
 ref=writer._add_object(font)
 for n in range(1,pages+1):
  page=writer.add_blank_page(width=595,height=842)
  page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):ref})})
  lines=[f'QA computer science document page {n}. SCCS{9000+n} EvidencePage{n:03d}', 'CapstoneDistributedSystemsFinalPage' if n==200 else 'Software engineering academic course information']
  lines += [f'Line {i} discusses computing systems software programming databases and curriculum research.' for i in range(12)]
  stream=DecodedStreamObject();stream.set_data(('BT /F1 10 Tf 30 800 Td '+' '.join('('+x+') Tj 0 -16 Td' for x in lines)+' ET').encode())
  page[NameObject('/Contents')]=writer._add_object(stream)
 if padded:
  extra=DecodedStreamObject();extra.set_data(b'X'*(9*1024*1024));writer._add_object(extra)
 out=io.BytesIO();writer.write(out);return out.getvalue()

@pytest.mark.parametrize('pages',[100,200,212,250])
def test_all_pages_extracted(tmp_path,pages):
 p=tmp_path/'long.pdf';p.write_bytes(pdf_fixture(pages))
 text=extract_pdf(p)
 assert text.count('[หน้า ')==pages
 assert f'EvidencePage{pages:03d}' in text and len(text)>60000
 chunks=split_evidence(text)
 assert all(len(c)<=1000 for c in chunks)
 assert f'EvidencePage{pages:03d}' in '\n'.join(chunks)


def test_pdf_rejections(tmp_path):
 p=tmp_path/'too-long.pdf';p.write_bytes(pdf_fixture(251))
 with pytest.raises(PDFValidationError,match='250'):extract_pdf(p)
 w=PdfWriter();w.add_blank_page(width=300,height=300);p=tmp_path/'scan.pdf'
 with p.open('wb') as f:w.write(f)
 with pytest.raises(PDFValidationError,match='ไม่พบข้อความ'):extract_pdf(p)
 p=tmp_path/'password.pdf';w=PdfWriter();w.add_blank_page(width=300,height=300);w.encrypt('qa-password')
 with p.open('wb') as f:w.write(f)
 with pytest.raises(PDFValidationError,match='รหัสผ่าน'):extract_pdf(p)


def test_long_lines_keep_tail():
 chunks=split_evidence('A'*6000+'END_MARKER')
 assert all(len(c)<=1000 for c in chunks)
 assert 'END_MARKER' in chunks[-1]


def test_200_page_upload_save_query_and_rollback(staff,monkeypatch):
 urls=[];item=None;started=time.monotonic()
 try:
  data=pdf_fixture(200,padded=True)
  r=staff.post('/api/uploads',files={'file':('qa-long.pdf',data,'application/pdf')});assert r.status_code==200,r.text
  url=r.json()['url'];urls.append(url)
  mid=staff.get('/api/auth/me').json()['major_ids'][0]
  payload={'degree_name':'QA วิทยาการคอมพิวเตอร์ long document','major_id':mid,'curriculum_year':2598,'file_url':url}
  r=staff.post('/api/manage/curricula',json=payload);assert r.status_code==200,r.text
  item=r.json()['id']
  with Session() as db:
   doc=db.scalar(select(Document).where(Document.record_type=='curricula',Document.record_id==item))
   assert doc.content.count('[หน้า ')==200 and 'EvidencePage200' in doc.content
   chunks=db.scalars(select(Chunk).where(Chunk.document_id==doc.id)).all()
   assert all(len(c.embedding)==768 for c in chunks)
   before=[c.id for c in chunks]
   sources=retrieve(db,'วิทย์คอม ปี 2598 SCCS9200 คือวิชาอะไร')
   assert sources and all(s['document_id']==doc.id for s in sources)
   assert 'CapstoneDistributedSystemsFinalPage' in sources[0]['text']
  # Identical save must avoid all embeddings and preserve chunk identities.
  import backend.rag as rag
  with monkeypatch.context() as m:
   m.setattr(rag,'embed',lambda _: (_ for _ in ()).throw(AssertionError('unexpected re-embedding')))
   r=staff.put(f'/api/manage/curricula/{item}',json=payload);assert r.status_code==200,r.text
  with Session() as db:
   after=list(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id)))
   assert sorted(before)==sorted(after)
  bad=staff.post('/api/uploads',files={'file':('251.pdf',pdf_fixture(251),'application/pdf')})
  urls.append(bad.json()['url'])
  r=staff.put(f'/api/manage/curricula/{item}',json={**payload,'file_url':urls[-1]})
  assert r.status_code==422 and '250' in r.json()['detail']
  with Session() as db:
   assert db.get(MODELS['curricula'],item).file_url==url
   assert sorted(db.scalars(select(Chunk.id).where(Chunk.document_id==doc.id)))==sorted(before)
  # Exceed upload limit: reject before persisting a file.
  names=set((ROOT/'data/uploads').iterdir())
  r=staff.post('/api/uploads',files={'file':('oversized.pdf',b'%PDF-'+b'x'*(32*1024*1024),'application/pdf')})
  assert r.status_code==413 and set((ROOT/'data/uploads').iterdir())==names
  (ROOT/'evidence/pdf-200-test.json').write_text(json.dumps({'pages':200,'bytes':len(data),'chunks':len(chunks),'seconds':round(time.monotonic()-started,2),'last_page_retrieved':True,'identical_save_reencoded':False,'rollback_201_pages':True},indent=2),encoding='utf-8')
 finally:
  if item:staff.delete(f'/api/manage/curricula/{item}')
  for url in urls:(ROOT/'data/uploads'/url.rsplit('/',1)[-1]).unlink(missing_ok=True)
