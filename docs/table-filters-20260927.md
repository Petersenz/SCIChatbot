# หัวตารางเรียงลำดับและตัวกรองหลังบ้าน — 27 กันยายน 2569

สถานะ: แก้ใน workspace แยกจาก Production; ยังไม่ commit/push/deploy เว็บจริงยังเป็น48e75d5. เก็บงาน conversation core ที่ commit แล้วและ frontend double-scroll ที่ค้างไว้ ไม่แก้ DB/API/สิทธิ์/ข้อมูลธุรกิจ

## สิ่งที่เปลี่ยน

- ใช้ TableControls/SortHeading ร่วมกันใน Management7หน้า: ผู้ใช้ สาขา ข้อมูลทั่วไป ข่าว หลักสูตร อาชีพ Intent และ Reports4หน้า: ภาพรวม การใช้งาน ความพึงพอใจ คำถามที่ตอบไม่ได้
- หัวคอลัมน์ข้อมูลเป็นปุ่ม: กดครั้งแรกน้อย→มาก/ก→ฮ ครั้งที่สองกลับลำดับ ครั้งที่สามคืนลำดับเดิม มีลูกศรและ aria-sort รองรับ keyboard ส่วนคอลัมน์จัดการไม่มี sort เพราะเป็นปุ่มการทำงาน
- ปุ่มตัวกรองไอคอน sliders สีเหลืองอ่อนตามแบรนด์ เปิดแผงในหน้า ไม่สร้าง modal ซ้อน มีป้ายทุกช่อง ปุ่มใช้ตัวกรอง ล้างตัวกรอง badgesจำนวนเงื่อนไข chipsล้างทีละข้อและจำนวนผลลัพธ์
- ข้อความค้นแยกตามคอลัมน์ ไม่ค้นด้วย JSON.stringifyทั้งrecord ปีหลักสูตร/สาขา/ประเภทหน่วยงาน/บทบาท/สถานะ/รูปแบบคำตอบเป็น dropdown เฉพาะค่าที่มีในรายการที่ผู้ใช้มีสิทธิ์เห็น ค่าไม่มีข้อมูลแสดง “ยังไม่ระบุ” เมื่อมีจริง
- เงินเดือน ค่าเล่าเรียน หน่วยกิต เป็นช่วงรวมขอบล่าง/บน เว้นด้านใดด้านหนึ่งได้ ไม่ถือnullเป็น0; ปฏิเสธตัวเลขติดลบและช่วงกลับด้าน เก็บผลเดิมจนใช้ตัวกรองที่ถูกต้อง
- วันที่ข่าว/แชทเป็นช่วงวันที่ กรองตามวันเวลาไทย; sortวันที่ตามtimestamp, sortตัวเลขเชิงตัวเลขแม้ส่งมาเป็นstring; nullอยู่ท้ายทั้งสองทิศทางและไม่แก้ลำดับต้นฉบับ
- กรองและsortก่อนแบ่งหน้า เปลี่ยนเงื่อนไขกลับหน้าแรกและclampเมื่อข้อมูลลดลง ไม่รีโหลดทั้งหน้าและไม่ยิงAPIทุกครั้ง; ใช้ข้อมูลทั้งหมดที่APIเดิมส่งมา ไม่ใช่เฉพาะหน้าปัจจุบัน
- รายงานคงdate-rangeโหลดข้อมูลและsummaryเดิม แสดงคำอธิบายว่าตัวกรองใหม่มีผลเฉพาะตารางและCSVในหน้าที่มีexport; CSVใช้ชุดrowsเดียวกับตารางรวมลำดับ
- แสดงปีหลักสูตรเป็น2570ไม่ใส่comma2,570. คงโครงสร้างหน้าบท3และบรรยากาศเรียบง่ายสำหรับวัยทำงาน; ไม่เพิ่มเมนู/ตารางฐานข้อมูล/แพ็กเกจ

ไฟล์ใหม่: frontend/components/ui/table-query.ts และ table-controls.tsx; เชื่อมในApp.tsxและCSSกลาง. tests/table-query.cjs รันจากfrontendด้วย `node ../tests/table-query.cjs`

## หลักฐาน

- Final Next production build + TypeScript + git diff --check ผ่าน
- Node harness22checksผ่าน: ตัวเลขstring/number,ascending/descending,null-last,naturalnameorder,ANDหลายช่อง,ช่วงรวมขอบ/ด้านเดียว,ปีที่มีจริง,missingfilter,timezoneBangkok,dateinclusive,empty,validation,non-mutating,reportboolean,labelสาขา
- Browserใช้fixture HTTP8131 + Next3130 ผ่านSSHlocalhost13130 แยกจากProduction auth/DB; หยุดpreviewเฉพาะprocessที่สร้างหลังจบ
- หน้าจัดการครบ7หน้า: careersเลือกเอกชน+10000–20000ได้6แถว เรียง20000→10000; invalid30000–20000เตือน/ไม่ใช้; Escapeจากinputปิดแผง. curriculaเลือกปี2570+CS+fee≤20000ได้2แถว ขึ้นปีเฉพาะ2564/2566/2570. users/majors/general/news/intentsกรองtextแต่ละหน้าได้1จาก2ตามfixture
- Reportsครบ4หน้า: unansweredเลือกยังไม่ตรวจได้11จาก16; keyboardEnterหัววันที่ได้aria-sortascending. dashboard/usage/satisfactionเลือกไม่ถูกใจได้10จาก31แต่ละหน้า
- หน้าท้ายcareerpage4→กรองไม่พบได้0;ล้างกลับ31รายการและหน้า1. เปิดตัวกรอง/หัวคอลัมน์ทุกหน้าที่กล่าวมา ไม่พบbrowserconsoleerror
- ตรวจภาพdesktopcareersและmobilecurricula; viewport375/320/768/812landscape root scrollWidth=clientWidth(หักscrollbarแล้ว360/305/753/797). ตารางเลื่อนได้ภายในกรอบ ไม่ทำrootล้น

## ข้อจำกัด

ทดสอบข้อมูลจำลอง ไม่ได้เขียนProduction/CRUDหรือส่งCSVแล้วอ่านไฟล์กลับ; CSVตรวจเส้นทางโค้ดใช้filtered/sortedrowsเดิม. ไม่ใช่รับรองทุกcombination/ทุกอุปกรณ์/large-datasetbenchmark. Reduced-motionมีCSSรองรับแต่ไม่ได้สลับOSpreference;คงธีมสว่างเดิมไม่มีการสร้างdarkmode. การเรียงลำดับทีละคอลัมน์ ไม่ใช่multi-columnsort. ตัวเลือกdropdownมาจากรายการทั้งชุดในหน้าตามสิทธิ์ ไม่หดตามตัวกรองอื่นระหว่างเลือก

ก่อนปล่อย: reviewชุดfrontendรวมpendingdouble-scrollและตรวจcandidateที่จะปล่อยจริง; backendconversationcoreมีผลทดสอบเดิมที่ต้องทบทวนหลังข้อมูลcareerrelationsเปลี่ยน ไม่รวมปล่อย backendโดยปริยาย
