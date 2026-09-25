import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
from unittest.mock import Mock
import httpx
import pytest
from backend import rag, generation_cache as cache
from backend.db import Session


@pytest.fixture(autouse=True)
def isolation(monkeypatch):
    cache.clear()
    monkeypatch.setattr(rag, '_last_calls', [])
    monkeypatch.setattr(rag.time, 'sleep', lambda _: None)
    yield
    cache.clear()


def test_cache_expiry_and_capacity(monkeypatch):
    monkeypatch.setattr(cache, 'LIMIT', 2)
    clock = [0]
    monkeypatch.setattr(cache.time, 'monotonic', lambda: clock[0])
    cache.put('a', {'x':1}); cache.put('b', 2); cache.put('c', 3)
    assert cache.get('a') is None
    clock[0] = 301
    assert cache.get('c') is None


def test_cache_copies_and_keys():
    value = [{'text':'หลักสูตร2570','url':'/records/curricula/24'}]
    key = cache.key_for('ถามปี2570', value, 'model')
    cache.put(key, value)
    cache.get(key)[0]['text']='changed'
    assert cache.get(key)==value
    assert key != cache.key_for('ถามปี2564',value,'model')
    assert key != cache.key_for('ถามปี2570',value,'other-model')
    assert key != cache.key_for('ถามปี2570',[{'text':'แก้ไข','url':'/records/curricula/24'}],'model')


def test_news_compaction_preserves_facts():
    text='ข่าวประชาสัมพันธ์\nโพสต์เมื่อ\n15 กันยายน 2569\nจำนวนผู้ชม\n123\nแชร์ข่าวนี้ลง Facebook\n\nกิจกรรม\n18 หน่วยกิต\n18 หน่วยกิต'
    result=rag.compact_evidence(text)
    assert '15 กันยายน 2569' in result
    assert result.count('18 หน่วยกิต')==2
    assert 'จำนวนผู้ชม' not in result and '123' not in result


def test_network_timeout_retries_once():
    call=Mock(side_effect=[httpx.ReadTimeout('timeout'),'ok'])
    assert rag.generate_with_retry(call)=='ok'
    assert call.call_count==2


def test_elapsed_budget_stops_retry(monkeypatch):
    clock=iter([0,20,20])
    monkeypatch.setattr(rag.time,'monotonic',lambda:next(clock))
    call=Mock(side_effect=httpx.ReadTimeout('timeout'))
    with pytest.raises(httpx.ReadTimeout): rag.generate_with_retry(call)
    assert call.call_count==1


@pytest.mark.parametrize('identifier,kind',[('GenerateRequestsPerDay','daily'),('GenerateRequestsPerMinute','per_minute'),('unknown','unknown')])
def test_quota_classification(identifier,kind):
    exc=SimpleNamespace(response_json={'error':{'details':[{'violations':[{'quotaId':identifier}]}]}})
    assert rag.quota_kind(exc)==kind
    assert rag.quota_kind(Exception('private provider message'))=='unknown'
    assert rag.quota_kind(SimpleNamespace(response_json={'error':{'details':None}}))=='unknown'


def test_cache_retrieves_again_and_invalidates_after_edit_delete(monkeypatch):
    from google import genai
    client=Mock(); client.models.generate_content.return_value.text='ข้อมูลที่บันทึก [1]'
    monkeypatch.setattr(genai,'Client',Mock(return_value=client))
    evidence=[{'title':'หลักฐาน','url':'/records/news/39','text':'เนื้อหาเดิม'}]
    retrieve=Mock(side_effect=lambda *_:[dict(s) for s in evidence])
    monkeypatch.setattr(rag,'retrieve',retrieve)
    with Session() as db:
        assert rag.answer(db,'Smart Start จัดที่ไหน',[])[4]=='gemini'
        assert rag.answer(db,'Smart Start จัดที่ไหน',[])[4]=='gemini_cached'
        assert client.models.generate_content.call_count==1 and retrieve.call_count==2
        evidence[0]['text']='เนื้อหาแก้ไข'
        assert rag.answer(db,'Smart Start จัดที่ไหน',[])[4]=='gemini'
        assert client.models.generate_content.call_count==2
        history=[SimpleNamespace(user_query='บริบทอื่น')]
        assert rag.answer(db,'Smart Start จัดที่ไหน',history)[4]=='gemini'
        evidence.clear()
        assert rag.answer(db,'Smart Start จัดที่ไหน',[])[4]=='no_evidence'


@pytest.mark.parametrize('response',['ไม่มีข้อมูล','คำตอบไม่มีcitation'])
def test_unsuccessful_answer_not_cached(monkeypatch,response):
    from google import genai
    client=Mock(); client.models.generate_content.return_value.text=response
    monkeypatch.setattr(genai,'Client',Mock(return_value=client))
    with Session() as db:
        for _ in range(2):
            assert rag.answer(db,'Smart Start 2569 จัดที่ไหน',[])[4]!='gemini_cached'
    assert client.models.generate_content.call_count==2
