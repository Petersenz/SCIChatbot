import pytest
from backend.db import Session
from backend.rag import retrieve, fallback_message


@pytest.mark.parametrize('question', [
    'อยากทราบเกี่ยวกับ สาขาวิทย์คอมครับ',
    'ช่วยแนะนำสาขาวิทคอมหน่อย',
    'ขอข้อมูลทั่วไป Computer Science',
    'อยากรู้จักสาขาวิทยาการคอมพิวเตอร์',
])
def test_broad_introduction_uses_managed_description(question):
    with Session() as db:
        rows = retrieve(db, question)
    assert len(rows) == 1 and rows[0]['url'] == '/records/curricula/75'
    assert 'แผนรับ 30 คน' in rows[0]['text']
    assert 'ตารางเปรียบเทียบ' not in rows[0]['text']


@pytest.mark.parametrize('question,path', [
    ('ขอข้อมูลเกี่ยวกับวิทย์คอม ปี2570 หน่วยกิตรวมตลอดหลักสูตร', '/records/curricula/24'),
    ('ขอข้อมูลเกี่ยวกับทุนวิทย์คอม', '/records/general/27'),
    ('ขอข้อมูลเกี่ยวกับอาจารย์วิทย์คอม', '/records/general/28'),
])
def test_specific_questions_are_not_replaced_by_introduction(question, path):
    with Session() as db:
        rows = retrieve(db, question)
    assert rows and all(row['url'] == path for row in rows)


def test_unknown_year_does_not_borrow_introduction():
    with Session() as db:
        assert retrieve(db, 'ขอข้อมูลวิทย์คอมปี2599') == []


def test_pdf_timeout_does_not_dump_internal_metadata():
    exc = RuntimeError('upstream')
    exc.code = 504
    message = fallback_message(exc, {'chunk_id': 1, 'title': 'หลักสูตร',
                                    'text': 'degree_name: x\n[หน้า 95]\nตารางเปรียบเทียบ'})
    assert 'ขัดข้อง' in message and 'แหล่งข้อมูล' in message
    assert 'degree_name' not in message and '[หน้า 95]' not in message


def test_partial_answer_keeps_valid_citations(monkeypatch):
    from unittest.mock import Mock
    from google import genai
    from backend import rag, generation_cache
    generation_cache.clear()
    client = Mock()
    client.models.generate_content.return_value.text = 'วิทยาศาสตรบัณฑิต ปี 2568 [1]\nไม่พบข้อมูลหน่วยกิตรวม'
    monkeypatch.setattr(genai, 'Client', Mock(return_value=client))
    monkeypatch.setattr(rag, '_last_calls', [])
    with Session() as db:
        body, sources, answered, _, mode = rag.answer(db, 'อยากทราบเกี่ยวกับ สาขาวิทย์คอมครับ', [])
    assert answered and mode == 'gemini'
    assert '[1]' in body and len(sources) == 1
    generation_cache.clear()
