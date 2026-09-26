"""CRUD and validation against ephemeral SQLite only; index boundary mocked.

Synthetic identities exist only in memory, never production accounts. Live
PostgreSQL retrieval and indexing are validated in separate suites.
"""
from types import SimpleNamespace as N
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from backend import main
from backend.db import Base,MODELS,User,Document,Auth,MajorUser,CurriculumCareer
from test_core_api_isolated import jsonb_sqlite,bigint_sqlite

@pytest.fixture
def management(monkeypatch):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine,tables=[m.__table__ for m in MODELS.values()]+[Document.__table__,Auth.__table__,MajorUser.__table__,CurriculumCareer.__table__])
    with Session(engine) as db:
        db.add_all([User(id=100,username='fixture_admin',fullname='Fixture',password='not-a-credential',role='admin',active=True),User(id=101,username='fixture_staff',fullname='Fixture',password='not-a-credential',role='staff',active=True)])
        db.add_all([MODELS['majors'](id=1,major_name_th='วิทยาการคอมพิวเตอร์'),MODELS['majors'](id=2,major_name_th='สาขาอื่น')])
        db.add(MajorUser(user_id=101,major_id=1));db.commit()
    actor=N(id=100,role='admin');indexed=[]
    def session():
        with Session(engine) as db:yield db
    main.app.dependency_overrides[main.db_session]=session
    main.app.dependency_overrides[main.current_user]=lambda:actor
    monkeypatch.setattr(main,'sync_doc',lambda entity,row,db:indexed.append((entity,row.id)) or [])
    client=TestClient(main.app,client=('management-fixture',50101))
    try:yield client,actor,indexed,engine
    finally:
        main.app.dependency_overrides.pop(main.db_session,None);main.app.dependency_overrides.pop(main.current_user,None);engine.dispose()

@pytest.mark.parametrize('entity,payload,key,staff',[
    ('majors',{'major_name_th':'Fixture new major'},'major_name_th',False),
    ('general',{'topic':'Fixture topic','description':'description'},'topic',False),
    ('news',{'title':'Fixture news','content':'content'},'title',False),
    ('intents',{'intent_name':'Fixture intent','action_type':'rule_based','static_response':'สวัสดีค่ะ','prompt_context':'fixture'},'intent_name',False),
    ('careers',{'job_title':'Fixture career','work_sector':'p','salary_start':12345.67},'job_title',True),
    ('curricula',{'degree_name':'Fixture curriculum','major_id':1,'curriculum_year':2570,'tuition_fee':8000,'total_credits':121,'career_ids':[]},'degree_name',True),
    ('users',{'fullname':'Fixture only','username':'fixture_new','password':'test-only-password','role':'staff','active':True,'major_ids':[1]},'fullname',False),
])
def test_create_edit_reload_delete(management,entity,payload,key,staff):
    client,actor,indexed,engine=management
    if staff:actor.role='staff';actor.id=101
    response=client.post('/api/manage/'+entity,json=payload)
    assert response.status_code==200,response.text
    id=response.json()['id']; payload={**payload,key:payload[key]+' updated'}
    if entity=='users':payload.pop('password')
    response=client.put(f'/api/manage/{entity}/{id}',json=payload)
    assert response.status_code==200,response.text
    listed=client.get('/api/manage/'+entity).json()
    assert next(row for row in listed if row['id']==id)[key]==payload[key]
    assert indexed.count((entity,id))==2
    assert client.delete(f'/api/manage/{entity}/{id}').status_code==200
    assert id not in [row['id'] for row in client.get('/api/manage/'+entity).json()]

def test_invalid_values_and_role_boundary_do_not_save(management):
    client,actor,indexed,engine=management
    for entity,payload in [('general',{'topic':'x','description':''}),('news',{'title':'x','content':''}),('intents',{'intent_name':'x','action_type':'rule_based','static_response':''}),('majors',{'major_name_th':'x','email':'invalid'})]:
        assert client.post('/api/manage/'+entity,json=payload).status_code==422
    actor.role='staff';actor.id=101
    assert client.get('/api/manage/users').status_code==403
    assert client.post('/api/manage/curricula',json={'degree_name':'x','major_id':2}).status_code==403
    for amount in [-1,1.001,'NaN',True]:
        assert client.post('/api/manage/careers',json={'job_title':'x','work_sector':'p','salary_start':amount}).status_code==422
    assert client.post('/api/manage/careers',json={'job_title':'x','work_sector':'invalid'}).status_code==422
    assert client.patch('/api/profile',json={'email':'invalid'}).status_code==422
    assert client.post('/api/uploads',files={'file':('fake.pdf',b'%PDF-broken','application/pdf')}).status_code==422
    assert not indexed

def test_curriculum_relation_replacement_and_staff_profile(management):
    client,actor,indexed,engine=management;actor.role='staff';actor.id=101
    job=client.post('/api/manage/careers',json={'job_title':'Fixture job','work_sector':'p'}).json()
    payload={'degree_name':'Fixture linked','major_id':1,'career_ids':[job['id']]}
    row=client.post('/api/manage/curricula',json=payload).json()
    assert row['career_ids']==[job['id']]
    response=client.put('/api/manage/curricula/'+str(row['id']),json={**payload,'career_ids':[]})
    assert response.status_code==200 and response.json()['career_ids']==[]
    response=client.patch('/api/profile',json={'fullname':'Updated fixture','email':'test@example.test','tel_no':'056123456'})
    assert response.status_code==200 and response.json()['fullname']=='Updated fixture'
