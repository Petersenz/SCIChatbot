from backend.response_style import RESPONSE_STYLE, format_answer


def test_plain_list_format_preserves_facts_and_citations():
    assert format_answer("**วิทย์คอม**\n\n\n* ปี 2570 [1]\n    * 18 หน่วยกิต\n- SCCS4105") == "วิทย์คอม\n\n• ปี 2570 [1]\n• 18 หน่วยกิต\n• SCCS4105"


def test_formatter_does_not_hide_missing_requested_data_or_change_identifiers():
    text = "ไม่พบข้อมูลค่าเทอมปี 2599\nค่าธรรมเนียม 8,000 บาท ไม่ระบุว่าต่อเทอม [1]\nSCCS-4105"
    assert format_answer(text) == text


def test_complete_lists_are_not_truncated():
    text = "\n".join(f"* อาชีพ {i} [1]" for i in range(1, 9))
    result = format_answer(text)
    assert result.count("• ") == 8 and "อาชีพ 8 [1]" in result


def test_guidance_scopes_omission_to_unasked_topics():
    assert "ผู้ใช้ไม่ได้ถาม" in RESPONSE_STYLE
    assert "ถามข้อมูลนั้นโดยตรง" in RESPONSE_STYLE
    assert "ไม่ตัดให้เหลือ 4 รายการ" in RESPONSE_STYLE
    assert "ค่าธรรมเนียมที่ไม่ได้ระบุว่าต่อเทอม" in RESPONSE_STYLE


def test_generated_answer_uses_style_and_keeps_source(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from google import genai
    from backend import rag, generation_cache
    class Rows(list):
        def all(self): return self
    class DB:
        def scalars(self, query): return Rows()
    generation_cache.clear()
    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-placeholder")
    monkeypatch.setenv("GEMINI_MODEL", "unit-test-model")
    monkeypatch.setattr(rag, "resolve_query", lambda db,q,h:q)
    monkeypatch.setattr(rag, "ambiguity", lambda *a:None)
    monkeypatch.setattr(rag, "retrieve", lambda *a:[{"title":"หลักสูตร", "url":"/records/curricula/24", "text":"หน่วยกิตรวม 121", "document_id":None, "chunk_id":None}])
    monkeypatch.setattr(rag, "with_images", lambda db,s:s)
    monkeypatch.setattr(rag, "_last_calls", [])
    client = Mock()
    client.models.generate_content.return_value.text = "* หน่วยกิตรวม 121 [1]"
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))
    body, sources, answered, _, mode = rag.answer(DB(), "ทั้งหลักสูตรมีกี่หน่วยกิต", [])
    prompt = client.models.generate_content.call_args.kwargs["contents"]
    assert RESPONSE_STYLE in client.models.generate_content.call_args.kwargs["config"].system_instruction
    assert RESPONSE_STYLE in prompt and prompt.index(RESPONSE_STYLE) < prompt.index("หลักฐาน:\n")
    assert body == "• หน่วยกิตรวม 121 [1]" and answered and mode == "gemini"
    assert len(sources) == 1
    generation_cache.clear()


def test_overview_budget_does_not_limit_specific_complete_answers():
    from backend.response_style import overview_style
    assert "650" in overview_style("สนใจเกี่ยวกับคอมพิวเตอร์ แนะนำหน่อยครับ")
    assert "650" in overview_style("อยากทราบเกี่ยวกับ สาขาวิทย์คอมครับ")
    for q in ["แนะนำอาชีพวิทย์คอมทั้งหมด", "แนะนำทุนวิทย์คอม", "ขอรายวิชาทั้งหมด", "แนะนำหลักสูตรแบบละเอียด"]:
        assert overview_style(q) == ""
