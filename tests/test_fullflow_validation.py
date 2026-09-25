"""Invalid form values must fail before touching real records or their indexes."""
import io
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from backend.main import app, clean, profile, report, resolve
from backend.db import Session, MODELS
from test_api import admin, staff


def test_form_validation_before_persistence():
    with Session() as db:
        user = SimpleNamespace(role='admin', id=-1)
        for entity, body in [
            ('majors', {'major_name_th':'QA', 'email':'not-an-email'}),
            ('majors', {'major_name_th':'QA', 'website_url':'https://[broken'}),
            ('majors', {'major_name_th':'QA', 'website_url':'https://user:pass@example.com'}),
            ('general', {'topic':'QA','description':'test','image_url':'/api/uploads/../missing.png'}),
            ('general', {'topic':'QA','description':'test','image_url':'/api/uploads/'+'a'*32+'.pdf'}),
            ('intents', {'intent_name':'QA','action_type':'rule_based','static_response':'   '}),
        ]:
            with pytest.raises(HTTPException) as error:
                clean(entity, body, db, user)
            assert error.value.status_code == 422


def test_file_and_profile_api_validation(staff):
    mid = staff.get('/api/auth/me').json()['major_ids'][0]
    before = staff.get('/api/auth/me').json()
    for url in ['https://example.com/photo.png','/api/uploads/'+'b'*32+'.png', '/api/uploads/'+'c'*32+'.pdf']:
        r=staff.post('/api/manage/curricula',json={'degree_name':'QA must not save','major_id':mid,'file_url':url})
        assert r.status_code==422, r.text
    assert staff.patch('/api/profile',json={'email':'invalid'}).status_code==422
    assert staff.get('/api/auth/me').json()['email']==before['email']
    for name,content,mime in [('fake.png',b'\x89PNGnot-an-image','image/png'),('fake.pdf',b'%PDF-not-a-pdf','application/pdf')]:
        assert staff.post('/api/uploads',files={'file':(name,content,mime)}).status_code==422


def test_report_date_and_resolution_types(admin):
    assert admin.get('/api/reports/usage?start=2026-09-25&end=2026-09-24').status_code==422
    with TestClient(app) as guest:
        guest.get('/api/conversations')
        cid=guest.post('/api/conversations').json()['id']
        try:
            for value in [None, {}, 42, ' ', 'x'*121]:
                assert guest.patch('/api/conversations/'+cid,json={'title':value}).status_code==422
            msg=guest.post('/api/conversations/'+cid+'/messages',json={'message':'วิทย์คอม ปี2599 หน่วยกิต'}).json()
            for value in ['false', 1, None]:
                assert admin.patch('/api/unanswered/'+str(msg['id']),json={'resolved':value}).status_code==422
            assert admin.patch('/api/unanswered/'+str(msg['id']),json={'resolved':True}).status_code==200
        finally:
            guest.delete('/api/conversations/'+cid)


def test_pdf_replace_rollback_and_delete(staff):
    from pathlib import Path
    from sqlalchemy import select, func
    from backend.db import ROOT, Document, Chunk
    from backend.rag import retrieve
    urls=[]; item_id=None; did=None
    try:
        from pypdf import PdfWriter
        from pypdf.generic import NameObject, DecodedStreamObject, DictionaryObject
        for marker in ['QA_FULLFLOW_A','QA_FULLFLOW_B']:
            writer=PdfWriter();page=writer.add_blank_page(width=300,height=300)
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
            stream=DecodedStreamObject();stream.set_data(f'BT /F1 12 Tf 10 100 Td ({marker} Academic guidance test document with evidence.) Tj ET'.encode())
            page[NameObject('/Contents')]=writer._add_object(stream);buf=io.BytesIO();writer.write(buf)
            r=staff.post('/api/uploads',files={'file':('qa.pdf',buf.getvalue(),'application/pdf')})
            assert r.status_code==200
            urls.append(r.json()['url'])
        mid=staff.get('/api/auth/me').json()['major_ids'][0]
        payload={'degree_name':'QA fullflow isolated curriculum','major_id':mid,'curriculum_year':2597,'total_credits':111,'file_url':urls[0]}
        r=staff.post('/api/manage/curricula',json=payload);assert r.status_code==200,r.text
        item_id=r.json()['id']
        with Session() as db:
            doc=db.scalar(select(Document).where(Document.record_type=='curricula',Document.record_id==item_id));did=doc.id
            assert 'QA_FULLFLOW_A' in doc.content
        r=staff.put('/api/manage/curricula/'+str(item_id),json={**payload,'file_url':urls[1],'total_credits':122});assert r.status_code==200
        with Session() as db:
            doc=db.get(Document,did);chunks=db.scalars(select(Chunk).where(Chunk.document_id==did)).all()
            assert 'QA_FULLFLOW_B' in doc.content and 'QA_FULLFLOW_A' not in doc.content
            assert any('QA_FULLFLOW_B' in c.content for c in chunks)
            assert all('QA_FULLFLOW_A' not in c.content and len(c.embedding)==768 for c in chunks)
        bad=staff.put('/api/manage/curricula/'+str(item_id),json={**payload,'file_url':'https://example.org/photo.png'})
        assert bad.status_code==422
        with Session() as db:
            assert db.get(MODELS['curricula'],item_id).total_credits==122
            assert 'QA_FULLFLOW_B' in db.get(Document,did).content
        assert staff.delete('/api/manage/curricula/'+str(item_id)).status_code==200
        item_id=None
        with Session() as db:
            assert db.get(Document,did) is None
            assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id==did))==0
            assert retrieve(db,'วิทย์คอม ปี2597 หน่วยกิตรวม')==[]
    finally:
        if item_id:staff.delete('/api/manage/curricula/'+str(item_id))
        for url in urls:(ROOT/'data/uploads'/url.rsplit('/',1)[-1]).unlink(missing_ok=True)


def test_profile_password_and_disabled_account(admin):
    import secrets
    body={'username':'qa_'+secrets.token_hex(8),'fullname':'QA isolated account','role':'staff','password':secrets.token_urlsafe(20),'active':True,'major_ids':[]}
    r=admin.post('/api/manage/users',json=body);assert r.status_code==200
    uid=r.json()['id'];new_password=secrets.token_urlsafe(20)
    try:
        with TestClient(app,client=('qa-profile-'+secrets.token_hex(6),50000)) as user:
            assert user.post('/api/auth/login',json={'username':body['username'],'password':body['password']}).status_code==200
            assert user.patch('/api/profile',json={'fullname':'QA profile updated','email':'qa@example.org','tel_no':'056717100'}).status_code==200
            assert user.get('/api/auth/me').json()['fullname']=='QA profile updated'
            assert user.patch('/api/profile',json={'current_password':'incorrect','new_password':new_password}).status_code==422
            assert user.patch('/api/profile',json={'current_password':body['password'],'new_password':new_password}).status_code==200
            assert user.get('/api/auth/me').status_code==401
            assert user.post('/api/auth/login',json={'username':body['username'],'password':body['password']}).status_code==401
            assert user.post('/api/auth/login',json={'username':body['username'],'password':new_password}).status_code==200
            assert user.post('/api/auth/logout').status_code==200
            assert user.get('/api/auth/me').status_code==401
            assert user.post('/api/auth/login',json={'username':body['username'],'password':new_password}).status_code==200
            assert admin.put('/api/manage/users/'+str(uid),json={**body,'password':'','active':False}).status_code==200
            assert user.get('/api/auth/me').status_code==401
    finally:
        assert admin.delete('/api/manage/users/'+str(uid)).status_code==200
