import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import date
from unittest.mock import Mock
import pytest
from backend import rag
from backend.db import Session
from backend.structured_evidence import published_date


def test_publication_not_event_or_import_date():
    assert published_date('โพสต์เมื่อ\n15 กันยายน. 2569\nวันที่ 14 กันยายน 2569') == date(2026, 9, 15)
    assert published_date('จัดเมื่อวันที่ 14 มิถุนายน 2569') is None
    assert published_date('โพสต์เมื่อ 31 กุมภาพันธ์ 2569') is None


@pytest.mark.parametrize('q', ['ข่าวล่าสุดของคณะวิทยาศาสตร์และเทคโนโลยีคือข่าวอะไร', 'ข่าวใหม่สุดของคณะ', 'มีข่าวอะไรล่าสุด'])
def test_latest_uses_published_date(q):
    with Session() as db:
        sources = rag.retrieve(db, q)
        assert [s['url'] for s in sources] == ['/records/news/10']
        assert '15 กันยายน' in sources[0]['text']
        assert 'ไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์' in sources[0]['text']


def test_images_from_selected_record_only():
    with Session() as db:
        selected = rag.with_images(db, [{'url':'/records/news/39'}, {'url':'/records/curricula/24'}])
        assert selected[0]['image_url'].startswith('/api/uploads/')
        assert 'image_url' not in selected[1]
        assert rag.with_images(db, []) == []


@pytest.fixture
def retry_state(monkeypatch):
    monkeypatch.setattr(rag, '_last_calls', [])
    monkeypatch.setattr(rag.time, 'sleep', lambda _: None)


class UpstreamError(Exception):
    def __init__(self, code): self.code = code


def test_transient_failure_recovers_once(retry_state):
    call = Mock(side_effect=[UpstreamError(503), 'ok'])
    assert rag.generate_with_retry(call) == 'ok'
    assert call.call_count == 2
    assert len(rag._last_calls) == 2


@pytest.mark.parametrize('code, attempts', [(503,2),(500,2),(429,1),(403,1),(400,1)])
def test_retry_is_bounded(retry_state, code, attempts):
    call = Mock(side_effect=UpstreamError(code))
    with pytest.raises(UpstreamError): rag.generate_with_retry(call)
    assert call.call_count == attempts


def test_local_limit_is_not_retried(retry_state):
    rag._last_calls[:] = [rag.time.time()] * 8
    call = Mock()
    with pytest.raises(RuntimeError, match='local_rate_limit'): rag.generate_with_retry(call)
    call.assert_not_called()


def test_exhausted_generation_returns_honest_fallback(monkeypatch, retry_state):
    from google import genai
    client = Mock()
    client.models.generate_content.side_effect = UpstreamError(503)
    monkeypatch.setattr(genai, 'Client', Mock(return_value=client))
    with Session() as db:
        body, sources, answered, _, mode = rag.answer(db, 'Smart Start 2569 จัดวันไหน และจัดที่ไหน', [])
    assert client.models.generate_content.call_count == 2
    assert mode == 'retrieval_only' and not answered
    assert 'บริการ AI ขัดข้องชั่วคราว' in body
    assert 'ไม่ยืนยันว่าเป็นข่าวล่าสุด' not in body
    assert [s['url'] for s in sources] == ['/records/news/39']
    assert sources[0]['image_url'].startswith('/api/uploads/')


def test_latest_answer_always_discloses_coverage(monkeypatch, retry_state):
    from google import genai
    client = Mock()
    client.models.generate_content.return_value.text = 'ข่าวล่าสุดคือการประเมิน EdPEx [1]'
    monkeypatch.setattr(genai, 'Client', Mock(return_value=client))
    with Session() as db:
        body, sources, answered, _, mode = rag.answer(db, 'ข่าวล่าสุดของคณะวิทยาศาสตร์และเทคโนโลยีคือข่าวอะไร', [])
    assert answered and mode == 'gemini'
    assert 'ยังไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์คณะ' in body
    assert [s['url'] for s in sources] == ['/records/news/10']


@pytest.mark.parametrize('code, wording', [(429,'ขีดจำกัด'),(503,'ขัดข้อง'),(504,'ขัดข้อง'),(400,'ยังสรุปคำตอบนี้ไม่ได้')])
def test_fallback_explains_failure_without_internal_news_prefix(code, wording):
    message = rag.fallback_message(UpstreamError(code), {'text':'ข่าวที่จัดเก็บในระบบ ไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์:\nข้อมูลกิจกรรม'})
    assert wording in message
    assert 'ยังไม่ได้สรุป' in message and 'ข้อมูลกิจกรรม' in message
    assert 'ไม่ยืนยันว่าเป็นข่าวล่าสุด' not in message


def test_latest_fallback_keeps_scope_and_marks_truncation():
    message = rag.fallback_message(UpstreamError(503), {'text':'ข่าวที่มีวันที่เผยแพร่ล่าสุดในข้อมูลที่จัดเก็บ:\n' + 'ก'*700})
    assert '…' in message
    assert 'ยังไม่ยืนยันว่าเป็นข่าวล่าสุดบนเว็บไซต์คณะ' in message
