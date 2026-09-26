from backend.response_style import polite_answer


def test_facts_citations_and_urls_are_preserved():
    result = polite_answer("ปี 2570 มี 121 หน่วยกิต [1]\nhttps://example.com/course?q=1")
    assert "ปี 2570 มี 121 หน่วยกิตค่ะ [1]" in result
    assert result.endswith("https://example.com/course?q=1")
    assert polite_answer(result) == result


def test_particles_are_bounded_and_questions_natural():
    assert polite_answer("สวัสดีครับ\nมี 121 หน่วยกิตครับ\nสอบถามเพิ่มได้ครับ").count("ค่ะ") == 2
    assert polite_answer("หมายถึงสาขาไหนครับ") == "หมายถึงสาขาไหนคะ"
    assert polite_answer("ยินดีช่วยค่ะ") == "ยินดีช่วยค่ะ"


def test_verbatim_quotes_and_fallback_evidence_remain_intact():
    quote = '“สวัสดีครับ”'
    assert quote in polite_answer("ตัวอย่าง " + quote)
    evidence = "ข้อความจากแหล่งข้อมูลที่ค้นพบ (ยังไม่ได้สรุป):\nชื่อเรื่อง สวัสดีครับ\n121 หน่วยกิต [1]"
    result = polite_answer("บริการขัดข้องชั่วคราว\n\n" + evidence)
    assert result.endswith(evidence)
    assert "บริการขัดข้องชั่วคราวค่ะ" in result


def test_empty_and_bullet_only_answers():
    assert polite_answer("") == ""
    assert polite_answer("• วิชา A [1]\n• วิชา B [2]") == "ข้อมูลที่พบมีดังนี้ค่ะ\n• วิชา A [1]\n• วิชา B [2]"


def test_final_boundary_covers_all_provider_and_static_paths(monkeypatch):
    from backend import rag
    source = [{"url": "/records/curricula/24"}]
    for mode in ("groq", "gemini", "groq_cached", "rule_based", "grounded", "clarification", "no_evidence", "retrieval_only"):
        monkeypatch.setattr(rag, "_answer", lambda *args: ("มี 121 หน่วยกิต [1]", source, True, 7, mode))
        body, sources, supported, intent, returned_mode = rag.answer(None, "test", [])
        assert body == "มี 121 หน่วยกิตค่ะ [1]"
        assert sources is source and supported and intent == 7 and returned_mode == mode
