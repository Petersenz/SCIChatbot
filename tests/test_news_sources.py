import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from sqlalchemy import text
from backend.db import Session
from backend.rag import retrieve, cited_sources


@pytest.mark.parametrize('question', [
    'Smart Start 2569 จัดวันไหน และจัดที่ไหน',
    'Smart Start 2569จัดวันไหน และจัดที่ไหน',
    'ข่าว Smart Start 2569 จัดวันไหน และจัดที่ไหน',
    'smart start 2569 มีกิจกรรมอะไรบ้าง',
    'SmartStart 2569 จัดที่ไหน',
])
def test_news_paraphrases_only_related_source(question):
    with Session() as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        sources = retrieve(db, question)
        assert [s['url'] for s in sources] == ['/records/news/39']
        assert '14 มิถุนายน 2569' in sources[0]['text']


def test_generic_preparation_event_is_ambiguous_after_cs_news_import():
    from backend.rag import answer
    with Session() as db:
        question='งานเตรียมความพร้อมนักศึกษาใหม่ 2569 จัดวันไหน'
        sources=retrieve(db, question)
        assert {s['url'] for s in sources}=={'/records/news/39','/records/news/53'}
        result=answer(db, question, [])
        assert result[-1]=='clarification' and not result[2]
        assert 'หลายรายการ' in result[0]


def test_named_event_missing_year_is_not_substituted():
    with Session() as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        assert retrieve(db, 'Smart Start 2599 จัดที่ไหน') == []


def test_citations_not_just_first_result():
    sources = [{'url':f'/source/{n}'} for n in range(1,5)]
    body, selected = cited_sources('คำตอบ [3] และข้อมูลอีกเรื่อง [1] [3]', sources)
    assert body == 'คำตอบ [2] และข้อมูลอีกเรื่อง [1] [2]'
    assert selected == [sources[0], sources[2]]
    assert cited_sources('คำตอบ [2]', sources) == ('คำตอบ [1]', [sources[1]])


@pytest.mark.parametrize('body', ['คำตอบไม่มีอ้างอิง','คำตอบ [0]','คำตอบ [9]'])
def test_invalid_citations_cannot_be_presented_as_success(body):
    with pytest.raises(ValueError): cited_sources(body, [{'url':'/source/1'}])
