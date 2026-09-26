"""Actual chat API/session flow against temporary SQLite; no live writes."""
import json
from types import SimpleNamespace as N
from sqlalchemy import create_engine, BigInteger
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend import main, rag
from backend.db import Base, MODELS, User, Auth, MajorUser, CurriculumCareer, Conversation, Chat


@compiles(JSONB, 'sqlite')
def jsonb_sqlite(type, compiler, **kwargs): return 'JSON'


@compiles(BigInteger, 'sqlite')
def bigint_sqlite(type, compiler, **kwargs): return 'INTEGER'


def test_session_context_source_projection_and_new_session_isolation(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    from sqlalchemy import event
    @event.listens_for(engine, 'connect')
    def jsonpath(connection, _):
        connection.create_function('jsonb_path_query_array', 2, lambda raw, path: json.dumps([s['url'] for s in json.loads(raw or '[]') if 'url' in s]))
    tables = [model.__table__ for model in MODELS.values()] + [Auth.__table__, MajorUser.__table__, CurriculumCareer.__table__, Conversation.__table__, Chat.__table__]
    Base.metadata.create_all(engine, tables=tables)
    with Session(engine) as db:
        db.add(MODELS['majors'](id=1, major_name_th='วิทยาการคอมพิวเตอร์'))
        db.add(MODELS['curricula'](id=1, degree_name='หลักสูตรทดสอบ', major_id=1))
        db.add(MODELS['careers'](id=1, job_title='นักพัฒนาเว็บ', salary_start=18000, skill_required='React'))
        db.add(CurriculumCareer(curriculum_id=1, career_id=1))
        db.add(MODELS['news'](id=1, title='First Camp 2570', content='จัดที่ห้อง A'))
        db.add(MODELS['news'](id=2, title='Second Camp 2570', content='จัดที่ห้อง B'))
        db.commit()
    def db_session():
        with Session(engine) as db: yield db
    main.app.dependency_overrides[main.db_session] = db_session
    def forbidden(*args, **kwargs): raise AssertionError('No external generation in API fixture')
    monkeypatch.setattr(rag, 'generate_with_retry', forbidden)
    monkeypatch.setattr(rag, 'embed', forbidden)
    client = TestClient(main.app, client=('core-fixture', 50000))
    try:
        assert client.get('/api/conversations').status_code == 200
        first = client.post('/api/conversations').json()['id']
        response = client.post(f'/api/conversations/{first}/messages', json={'message': 'วิทย์คอมทำเว็บเงินเดือนเท่าไหร่'})
        assert response.status_code == 200, response.text
        assert '18,000' in response.json()['bot_response']
        response = client.post(f'/api/conversations/{first}/messages', json={'message': 'ต้องมีทักษะอะไรบ้าง'})
        assert response.status_code == 200 and 'React' in response.json()['bot_response']
        second = client.post('/api/conversations').json()['id']
        response = client.post(f'/api/conversations/{second}/messages', json={'message': 'เงินเดือนเท่าไหร่'})
        assert response.status_code == 200 and response.json()['answer_mode'] == 'clarification'
        other = TestClient(main.app, client=('other-core-fixture', 50000))
        other.get('/api/conversations')
        assert other.get(f'/api/conversations/{first}').status_code in (403, 404)
        with Session(engine) as db:
            monkeypatch.setattr(rag, 'identity', lambda: ('groq', 'fixture'))
            monkeypatch.setattr(rag, 'GroqClient', lambda: N(models=N(generate_content=lambda **kw: N(text='จัดที่ห้อง B [1]')), close=lambda: None))
            monkeypatch.setattr(rag, 'generate_with_retry', lambda fn: fn())
            body, sources, supported, _, mode = rag.answer(db, 'อันที่สองจัดที่ไหน', [N(user_query='มีข่าวอะไรบ้าง', sources=[{'url': '/records/news/1'}, {'url': '/records/news/2'}])])
            assert supported and 'ห้อง B' in body and [s['url'] for s in sources] == ['/records/news/2']
    finally:
        main.app.dependency_overrides.pop(main.db_session, None)
        engine.dispose()
