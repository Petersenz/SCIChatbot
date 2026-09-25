import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from sqlalchemy import select
from backend.db import Session, MODELS
from backend.query_understanding import resolve, ambiguity, TERM
import re
from backend.rag import retrieve

SEQUENCE=['Smart Start 2569 จัดวันไหน และจัดที่ไหน','วิทย์คอม ปี 2570 เทอมแรกเรียนอะไรบ้าง','แล้วเทอมสองหล่ะ','ทั้งหลักสูตรมีกี่หน่วยกิต','หน่วยกิตรวมตลอดหลักสูตร']


def test_exact_user_sequence_and_long_followups():
    with Session() as db:
        majors=list(db.scalars(select(MODELS['majors'])))
        history=[]
        for question in SEQUENCE+['หน่วยกิตรวมตลอดหลักสูตร']*5:
            resolved=resolve(question,history,majors)
            if question in SEQUENCE[3:]:
                assert 'วิทยาการคอมพิวเตอร์' in resolved and '2570' in resolved
                assert 'เทอม 2' not in resolved and 'ปีที่ 1' not in resolved
                sources=retrieve(db,resolved)
                assert [s['url'] for s in sources]==['/records/curricula/24']
                assert '121 หน่วยกิต' in sources[0]['text']
            history.append(SimpleNamespace(user_query=question))


def test_new_session_and_switches_do_not_inherit_old_major():
    with Session() as db:
        majors=list(db.scalars(select(MODELS['majors'])))
        assert ambiguity(resolve(SEQUENCE[-1],[],majors),majors)
        history=[SimpleNamespace(user_query=q) for q in SEQUENCE]
        switched=resolve('ไอที ปี 2564 ทั้งหลักสูตรมีกี่หน่วยกิต',history,majors)
        assert 'วิทยาการคอมพิวเตอร์' not in switched and '2570' not in switched
        assert 'เทคโนโลยีสารสนเทศ' in switched
        different_year=resolve('วิทย์คอม ปี 2564 ทั้งหลักสูตรมีกี่หน่วยกิต',history,majors)
        assert '2570' not in different_year
        assert '128' in retrieve(db,different_year)[0]['text']


def test_term_total_still_keeps_term():
    with Session() as db:
        majors=list(db.scalars(select(MODELS['majors'])))
        history=[SimpleNamespace(user_query=q) for q in SEQUENCE[:3]]
        q=resolve('กี่หน่วยกิต',history,majors)
        assert re.search(TERM,q).group(1)=='2' and '2570' in q


def test_api_loads_only_current_session_beyond_four_turns(monkeypatch):
    from fastapi.testclient import TestClient
    from backend import main
    import uuid
    seen=[]
    def fake_answer(db,q,history):
        seen.append([h.user_query for h in history])
        return 'ทดสอบบริบท',[],True,None,'rule_based'
    monkeypatch.setattr(main,'answer',fake_answer)
    client=TestClient(main.app,client=('scope-'+uuid.uuid4().hex,50000))
    client.get('/api/conversations')
    ids=[]
    try:
        for _ in range(2):
            ids.append(client.post('/api/conversations').json()['id'])
        for i in range(7):
            assert client.post(f'/api/conversations/{ids[0]}/messages',json={'message':f'คำถาม{i}'}).status_code==200
        assert seen[-1]==[f'คำถาม{i}' for i in range(6)]
        client.post(f'/api/conversations/{ids[1]}/messages',json={'message':'บทสนทนาใหม่'})
        assert seen[-1]==[]
    finally:
        for identifier in ids: client.delete(f'/api/conversations/{identifier}')
