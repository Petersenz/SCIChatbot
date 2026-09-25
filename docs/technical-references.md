# แหล่งอ้างอิงเทคนิคสำหรับจัดบรรณานุกรม

ตรวจแหล่งทางการ 24 กันยายน 2569 เอกสารนี้เป็นบันทึกสำหรับผู้จัดทำเล่ม ไม่ได้แก้บรรณานุกรมหรือต้นฉบับสามบท และไม่ใช่แบบประเมินความพึงพอใจ/ผลวิจัยจากกลุ่มตัวอย่าง

| แหล่ง | เทคนิคที่ใช้ในระบบ | หลักฐานในโค้ด/การทดสอบ | ขอบเขตที่อ้างได้ |
|---|---|---|---|
| W3C. (2023). Web Content Accessibility Guidelines (WCAG) 2.2. https://www.w3.org/TR/WCAG22/ และ https://www.w3.org/WAI/WCAG22/quickref/ | ป้ายฟอร์ม, คีย์บอร์ด, focus, แจ้งข้อผิดพลาด, contrast, responsive | App.tsx/style.css; axe ในหน้าและฟอร์มที่ตรวจ พร้อมภาพ desktop/mobile | ตรวจอัตโนมัติเป็นเพียงบางเกณฑ์ ไม่ใช่ใบรับรอง WCAG AA ทั้งระบบ |
| OWASP Foundation. (ม.ป.ป.). Input Validation Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html | ตรวจข้อมูลฝั่งเซิร์ฟเวอร์ทั้งชนิด รูปแบบ ช่วงค่า ค่าในชุดที่อนุญาต และความสัมพันธ์ | main.clean/profile/relations; test_fullflow_validation.py, test_api.py | ลดข้อมูลผิดรูปแบบ ไม่ได้ยืนยันว่าอีเมลมีเจ้าของจริงหรือค่าเล่าเรียนเป็นข้อเท็จจริง |
| OWASP Foundation. (ม.ป.ป.). File Upload Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html | จำกัดนามสกุล ขนาด ตรวจลายเซ็นและอ่านไฟล์จริง ตั้งชื่อสุ่ม ตรวจชนิดให้ตรงช่องแนบ | main.upload/validate_attachment; text_processing.inspect_pdf | ใช้แนวทางหลายชั้นที่ระบุ ไม่ได้อ้างว่ามี antivirus/CDR/OCR |
| Google. (ม.ป.ป.). Rate limits — Gemini API. https://ai.google.dev/gemini-api/docs/rate-limits | แยกปัญหาโควตาออกจากการค้นคืน ไม่retry429ซ้ำ และแจ้งว่าผลสำรองยังไม่ใช่คำตอบสรุป | rag.quota_kind, log status/attempt/quota; test_generation_stability.py | โควตาของบัญชีขึ้นกับผู้ให้บริการ ไม่รับรองว่าระบบตอบด้วยAIได้ตลอดเวลา |
| Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. https://arxiv.org/abs/2005.11401 | ค้นหลักฐานจากคลังเอกสารก่อนให้โมเดลสร้างคำตอบ | rag.retrieve/answer, documents/document_chunks, embeddings | ใช้อธิบายหลักการ RAG; การกรองสาขา ปี เทอม และหมายเลขอ้างอิงเป็นรายละเอียดการพัฒนาของโครงการ ไม่อ้างว่างานนี้พิสูจน์วิธีเฉพาะทั้งหมด |

ในการเขียนเล่ม ให้จัดรูปแบบผู้แต่ง/วันที่เข้าถึงให้ตรงคู่มือมหาวิทยาลัย และตรวจรายการเดิมไม่ให้ซ้ำ ผลทดสอบเชิงวิศวกรรมใน fullflow-audit-20260924.md ต้องแยกจากผลประเมินระบบและความพึงพอใจที่ยังไม่ได้เก็บจริง
