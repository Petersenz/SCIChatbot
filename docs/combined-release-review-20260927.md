# ผลปล่อยและรีวิว SCI Chatbot — 27 กันยายน 2569

## รุ่นที่ใช้งาน

- URL: https://cstack.space/sci-chatbot/
- Application SHA: `20600067a1c7af03e033018481716f617fe82cac`
- GitHub branch: `fix/context-scoped-retrieval` (ตรวจ remote SHA ตรงกัน; ไม่ merge main)
- เวลา activate: 2026-09-26 21:03:22 UTC / 27 กันยายน 04:03:22 น. ไทย
- รุ่น rollback: `48e75d5666cc36da0fd586c8d027c74f5986a722` เก็บไว้ครบ
- เปลี่ยน current symlink แบบ atomic และ restart เฉพาะ SCI API/web หลังตรวจว่าไม่มี connection กำลังทำงาน มีช่วงหยุดบริการสั้นระหว่าง restart ไม่ใช่ zero-downtime
- ไม่มี migration, dependency, provider/env, Nginx หรือข้อมูลธุรกิจเปลี่ยนในชุดนี้

## สิ่งที่ปล่อย

1. ระบบวางแผนค้นคืนร่วมตามหัวข้อ/เจตนา/สิ่งที่กำลังพูดถึงจากห้องเดียวกัน ครอบคลุมตารางสาธารณะที่มีอยู่ ไม่ใช้ข้อความ AI เก่าเป็นข้อเท็จจริง
2. กรองความสัมพันธ์หลักสูตร–อาชีพก่อน similarity; ถามเงินเดือนต่อจากงานเว็บได้เฉพาะงานเว็บพร้อมชื่อสาขา และรักษาคำอธิบายประมาณการ/ระดับประสบการณ์
3. Intent แบบ exact ก่อน semantic สำหรับคำสั้น ใช้ตัวอย่างที่ตั้งไว้และเกณฑ์ความมั่นใจ; ไม่เพิ่มตัวอย่างหรือแก้ข้อมูล Intent จริงรอบนี้
4. หัวตาราง sort และกลุ่มตัวกรองใน 7 หน้าจัดการ/4 หน้ารายงาน: dropdown จากค่าที่มีจริง ช่วงตัวเลข/วันที่ ตัวกรองหลายช่องร่วมกัน ล้างค่า และ pagination/CSV ตามรายการกรอง
5. แก้ root page scroll ซ้อน chat scroll; ช่องพิมพ์อยู่ในพื้นที่หน้าจอ
6. ฟอร์มแจ้งก่อนทิ้งร่างและป้องกัน Escape/ปิดระหว่างบันทึกหรืออัปโหลด; error เปลี่ยนชื่อ/ลบแสดงใน dialog และกันกดซ้ำ; แยกบันทึกสำเร็จจากโหลดรายการล้มเหลว

## ผลรีวิวอิสระที่แก้แล้ว

Code reviewer พบ 6 กรณี: ขยายคำถามระดับคณะแล้วยังติดสาขาเดิม, ขอทุกอาชีพแล้วยังติดงานเดิม, ไม่มีข้อมูลตรงขอบเขตแล้วหลุดไป vector อื่น, ถามหลายหมวดแล้วตอบเพียงหมวดเดียว, guard กระทบข่าวรับสมัคร, ติดต่อสาขาที่ไม่มีช่องติดต่อแต่ยังส่งชื่อเป็นหลักฐาน ทั้งหมดแก้พร้อม regression และ reviewer ตรวจซ้ำ 9 กรณีผ่าน

การถามค่าเทอมและเงินเดือนพร้อมกันยังใช้การถามกลับให้เลือกเรื่องก่อน ไม่ใช่ความสามารถตอบหลายหมวดในครั้งเดียว

UI reviewer พบ 4 ปัญหาการปิดฟอร์ม/ร่างหาย/error ซ่อน/การแจ้งผลหลังลบ แก้ในชุดนี้ Root ทดสอบ inline discard: กลับไปแก้แล้วข้อความยังอยู่, Escape ระหว่างบันทึกไม่ปิด, จำลอง503แสดงใน dialog และปลดปุ่ม, ทิ้งร่างแล้วปิดได้; rename503แสดงในกล่องและ Escape ระหว่างบันทึกไม่ปิด การลบจริงบน Production ไม่ได้ทดสอบ

## หลักฐานทดสอบและขอบเขต

| ระดับ | ผล | ข้อจำกัด |
|---|---|---|
| Backend รวม | 182 passed, 1 deselected, 1 dependency deprecation warning | ยกเว้น test เดิมที่เขียน Production; มี isolated API session test ทดแทนขอบเขตนั้น |
| CRUD isolated เพิ่มเติม | 9 passed | SQLite แยก, 7 entities create/update/read/delete, validation และสิทธิ์; mock เฉพาะ index boundary ไม่ใช่ real upload-to-vector ทั้ง flow |
| Frontend | production build/TypeScript ผ่าน, 22 table-query checks; request timing/error และ source rendering harness ผ่าน | ไม่ใช่ benchmark ปริมาณข้อมูลมหาศาล |
| UI fixture | 7 management +4 reports +profile; public/login/rating/rename, 375pxทั้ง12หน้าและ320pxfilterผ่านโดย reviewer | ข้อมูล/บทบาทจำลอง ไม่ใช่ยืนยันสิทธิ์จริง |
| ค้นคืนข้อมูลจริงหลัง deploy | 15/15 บน immutable release ใน transaction read-only | ไม่เรียก LLM, ไม่ยืนยันความสด/ความถูกต้องทางวิชาการของต้นทาง |
| สิทธิ์/ข้อมูลเว็บจริง | admin8/staff4รายการ API อ่านผ่าน;21อาชีพมีเงินเดือน; login/logoutผ่าน | ไม่แก้ business records จริง |
| หน้าเว็บจริง | วิทย์คอมทำเว็บ → เงินเดือน: อ้าง career3 เท่านั้นและระบุสาขา; thinking/answer/source/loginผ่าน; console errors0 | คำตอบแรกเรียกโมเดลจริงหนึ่งกรณี; ไม่รับรองทุกคำถาม/ทุกprovider |
| Chat layout เว็บจริง | root720/viewport720, rootY0; ภาพช่องพิมพ์อยู่หน้าจอ | viewport override รอบสุดท้ายไม่เปลี่ยนขนาดจริง จึงไม่อ้างผล mobile ใหม่; ใช้ผล reviewer ที่ระบุวันที่ |
| Infra | DB health true70documents837chunks; SCI2unitsactive; error-priority journalไม่มีรายการ;3เว็บเดิม200และไฟล์/Nginxhashก่อนหลังเท่ากัน | สุขภาพช่วงตรวจ ไม่ใช่ uptime/SLA |

คำสั่งทดสอบ public API ที่จะสร้างห้อง/ส่งข้อความ/rating/feedback/ลบห้องถูก automatic approval review ปฏิเสธก่อนรัน โดยให้เหตุผลเพียง blocked by policy; ไม่ retry ผ่านช่องทางอื่นและไม่อ้างว่า flow นี้ผ่าน หลังเหตุการณ์ตรวจต่อแบบอ่านอย่างเดียว การทดสอบ browser2ข้อความเกิดก่อนคำสั่งถูกปฏิเสธและยังอยู่ในประวัติ ไม่ลบประวัติผู้ใช้

ปัญหา fixture/test ที่แก้: test partial citation เดิมไม่เข้า generation เพราะมี deterministic answer อยู่แล้ว จึงแยก boundary ที่ต้องการทดสอบและรักษา assertion; native confirm ทำให้ browser automation ค้าง เปลี่ยนเป็น inline confirmation แล้วตรวจจริงผ่าน ไม่อ้างว่า native dialog ของผู้ใช้เสีย

## รายการควรปรับต่อ (ยังไม่ทำ ไม่ใช่ blocker ชุดนี้)

1. **P2 accessibility:** mobile admin drawer ควรปิดด้วย Escape, กัก focus และคืน focus แบบเดียวกับ public drawer
2. **P3 validation:** Intent ชนิด rule_based แสดง required ของคำตอบเตรียมไว้ให้ตรง backend; ตอนนี้ API ยังป้องกันค่าว่างอยู่
3. **P3 usability:** ค้นหาในรายการ checkbox อาชีพของหลักสูตรและแสดงจำนวนที่เลือก เพื่อไม่ต้องเลื่อนฟอร์มยาว
4. **P3 clarity:** helper ปี พ.ศ./หน่วยเงินเดือนต่อเดือน/ค่าเทอม และ source URL/ขนาดภาพให้ชัด; ไม่กำหนดปีขั้นต่ำสูงสุดทางธุรกิจเอง
5. **P3 accessibility:** validation ภาษาไทยและลิงก์ focus ไปช่องผิด; การเลือกไฟล์เกินขนาดซ้ำควร reset input
6. **ข้อมูลต้นทาง:** ยืนยันปีหลักสูตร/ปีรับเข้า ค่าเทอม และความเหมาะสมของ21อาชีพกับหลักสูตร; relationครบไม่เท่ากับข้อมูลวิชาการถูกต้องครบ
7. **Acceptance คงค้าง:** real staff UI CRUD/upload→index→RAG, replacement/delete indexing และ feedback/rating/report persistence บนเส้นทางที่ได้รับอนุมัติให้ทดสอบ ไม่ใช้ผล mock แทน

ไม่มีการแก้ต้นฉบับ3บท เพิ่มเมนู ตาราง หรือบทบาท ทุกข้อเสนอรักษาโครงหน้าเดิม

## เอกสารประกอบ

- `independent-code-review-20260927.md`: รายละเอียดเหตุ/ขอบเขตและผลรีวิว code
- `independent-ui-review-20260927.md`: รายหน้ากับรายการ UI-01–10 (สถานะหลัง root แก้ให้อ่านรายงานนี้ร่วมด้วย)
- `table-filters-20260927.md`: ตารางทดสอบตัวกรอง/sort
- หลักฐานเครื่องใน `tmp/combined-release/`: release JSON, combined-final.xml, deployed-core-backtest.json

Rollback: atomic current กลับไป release48e75d5 แล้ว restart เฉพาะ sci-chatbot-api/web และตรวจhealth/URL; ไม่มีDBmigrationจึงไม่ต้องย้อนข้อมูล เก็บทั้งสองreleaseไว้ ไม่แก้Nginx
