# SCI Chatbot

เว็บแชทบอทแนะแนวคณะวิทยาศาสตร์และเทคโนโลยี มหาวิทยาลัยราชภัฏเพชรบูรณ์ ใช้ NLP และ RAG จากข้อมูลที่จัดเก็บในระบบ ปัจจุบันเน้นตรวจความครบถ้วนของสาขาวิทยาการคอมพิวเตอร์ก่อนขยายข้อมูลสาขาอื่น

## เทคโนโลยี

- Next.js / React / TypeScript สำหรับหน้าเว็บ
- Python / FastAPI สำหรับ API
- PostgreSQL พร้อม pgvector (เวกเตอร์ 768 มิติ)
- Sentence Transformers: paraphrase-multilingual-mpnet-base-v2 สำหรับ embedding
- Gemini API สำหรับสรุปคำตอบตามหลักฐาน

## สิ่งที่อยู่ใน repository

โค้ดเว็บและ API, โลโก้, ชุดทดสอบ, รายการ dependencies และสคริปต์เปิด/ปิดระบบบน Windows ไม่มีฐานข้อมูลจริง บัญชีผู้ใช้ API key ประวัติสนทนา PDF/รูปที่อัปโหลด หรือผลทดสอบที่มีข้อมูลจากเครื่องผู้พัฒนา

## เตรียมรันในเครื่อง

1. ติดตั้ง Python (เครื่องพัฒนาใช้ 3.13), Node.js และ PostgreSQL ที่รองรับ pgvector
2. สร้างฐานข้อมูลสำหรับพัฒนาและเปิด extension `vector` ด้วยบัญชีที่มีสิทธิ์เหมาะสม
3. สร้าง virtual environment ชื่อ `.venv` แล้วติดตั้ง `backend/requirements.txt`
4. คัดลอก `.env.example` เป็น `.env` กำหนด `DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `EMBEDDING_MODEL` และ `SESSION_SECRET` ของตนเอง ห้าม commit ค่าจริง
5. ดาวน์โหลดโมเดล embedding ลง cache ของผู้ใช้ที่จะรัน backend ก่อนเริ่มระบบ เพราะโค้ดโหลดโมเดลแบบ `local_files_only=True`
6. ใน `frontend` รัน `npm ci` แล้ว `npm run build`
7. Windows ใช้ `./Start-SCI.ps1` เปิดเว็บที่ `http://127.0.0.1:3100` และ `./Stop-SCI.ps1` ปิดเฉพาะ process ของแอป

การรันบนระบบอื่น: backend ใช้ `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8010`; frontend ใช้ `npm run start` จากโฟลเดอร์ `frontend` (ตั้งค่า proxy ไป backend บนเครื่องเดียวกัน)

การเริ่ม backend สร้างตารางที่ยังไม่มี แต่ไม่ได้สร้างบัญชีหรือข้อมูลตัวอย่างให้เอง ต้องเตรียมข้อมูลและบัญชีผ่านกระบวนการที่ได้รับอนุญาต หรือ restore ฐานข้อมูลพร้อมไฟล์แนบแยกจาก Git ก่อนทดสอบเส้นทางที่ต้องล็อกอิน

## การทดสอบและข้อจำกัด

- `npm run build` ใน `frontend` ตรวจ build และ TypeScript
- ชุด `tests/` มีทั้ง unit และ integration tests บางชุดต้องใช้ฐานข้อมูลทดสอบที่มีข้อมูล CS และ `data/local-accounts.json` ภายในเครื่อง จึงยังไม่ใช่ชุดที่ clone แล้วรันทั้งหมดบนฐานข้อมูลว่างได้
- Integration tests มีการเพิ่ม/แก้ไข/ลบข้อมูลทดสอบ ให้ใช้ฐานข้อมูลสำหรับทดสอบเท่านั้น ไม่ใช้ฐานข้อมูล Production
- ผลทดสอบ Local ไม่รับรองว่าทุกคำถามตอบถูกหรือพร้อมใช้งานจริงบน VPS
- Gemini อาจตอบ 429/503/504 ระบบแยกคำตอบสำรองจากการตอบด้วย AI; การย้ายเครื่องไม่ได้รับรองว่าปัญหาบริการภายนอกจะหาย

## สถานะ deploy

Repository นี้ยังไม่มีชุด deploy VPS ที่ผ่านการตรวจจริง ต้องเตรียม service, reverse proxy/HTTPS, การสำรอง/กู้คืน DB และไฟล์แนบ, secrets และทรัพยากร embedding ก่อน deploy ไม่ใช่เว็บ static ที่อัปโหลด build อย่างเดียวแล้วใช้งานได้

แหล่งอ้างอิงเทคนิคสำหรับรายงานอยู่ใน `docs/technical-references.md` ต้นฉบับรายงานสามบทไม่ได้รวมอยู่ใน repository
