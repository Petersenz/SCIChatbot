export type Field = {
  key: string;
  label: string;
  type?: string;
  required?: boolean;
  options?: [string, string][];
};
export type Config = {
  title: string;
  single: string;
  fields: Field[];
  columns: string[];
};
const f = (
  key: string,
  label: string,
  type = "text",
  required = false,
  options?: [string, string][],
): Field => ({ key, label, type, required, options });
export const configs: Record<string, Config> = {
  majors: {
    title: "จัดการข้อมูลสาขาวิชา",
    single: "สาขาวิชา",
    columns: ["major_name_th", "major_name_en", "tel"],
    fields: [
      f("major_name_th", "ชื่อสาขาวิชา (ภาษาไทย)", "text", true),
      f("major_name_en", "ชื่อสาขาวิชา (ภาษาอังกฤษ)"),
      f("description", "รายละเอียด", "textarea"),
      f("tel", "เบอร์โทรศัพท์"),
      f("email", "อีเมล", "email"),
      f("facebook_page", "Facebook", "url"),
      f("website_url", "เว็บไซต์", "url"),
    ],
  },
  users: {
    title: "จัดการข้อมูลผู้ใช้",
    single: "ผู้ใช้",
    columns: ["fullname", "username", "role", "email"],
    fields: [
      f("fullname", "ชื่อ–นามสกุล", "text", true),
      f("username", "ชื่อผู้ใช้", "text", true),
      f("password", "รหัสผ่าน", "password"),
      f("role", "บทบาท", "select", true, [
        ["admin", "ผู้ดูแลระบบ"],
        ["staff", "เจ้าหน้าที่"],
      ]),
      f("email", "อีเมล", "email"),
      f("tel_no", "เบอร์โทรศัพท์"),
      f("major_ids", "สาขาวิชาที่รับผิดชอบ", "majors"),
      f("active", "เปิดใช้งาน", "checkbox"),
    ],
  },
  general: {
    title: "จัดการข้อมูลทั่วไปของคณะวิทยาศาสตร์และเทคโนโลยี",
    single: "ข้อมูลทั่วไป",
    columns: ["topic", "description"],
    fields: [
      f("topic", "หัวข้อ", "text", true),
      f("description", "รายละเอียด", "textarea", true),
      f("image_url", "รูปภาพ", "upload"),
    ],
  },
  news: {
    title: "จัดการข้อมูลข่าวสาร",
    single: "ข่าวสาร",
    columns: ["title", "content", "created_at"],
    fields: [
      f("title", "หัวข้อข่าว", "text", true),
      f("content", "เนื้อหาข่าว", "textarea", true),
      f("cover_image", "ภาพปก", "upload"),
    ],
  },
  curricula: {
    title: "จัดการหลักสูตร",
    single: "หลักสูตร",
    columns: [
      "degree_name",
      "major_id",
      "curriculum_year",
      "total_credits",
      "tuition_fee",
    ],
    fields: [
      f("degree_name", "ชื่อปริญญา / หลักสูตร", "text", true),
      f("major_id", "สาขาวิชา", "major", true),
      f("curriculum_year", "ปีหลักสูตร (พ.ศ.)", "number"),
      f("total_credits", "จำนวนหน่วยกิตรวม", "number"),
      f("tuition_fee", "ค่าธรรมเนียมการศึกษา/เทอม", "number"),
      f("description", "รายละเอียดหลักสูตร", "textarea"),
      f("file_url", "ไฟล์หลักสูตร (PDF)", "upload"),
      f("career_ids", "อาชีพหลังจบการศึกษา", "careers"),
    ],
  },
  careers: {
    title: "จัดการอาชีพ",
    single: "อาชีพ",
    columns: ["job_title", "work_sector", "salary_start", "skill_required"],
    fields: [
      f("job_title", "ชื่ออาชีพ", "text", true),
      f("job_description", "ลักษณะงาน", "textarea"),
      f("work_sector", "ประเภทหน่วยงาน", "select", true, [
        ["g", "ภาครัฐ"],
        ["p", "เอกชน"],
        ["o", "ธุรกิจส่วนตัว"],
        ["s", "รัฐวิสาหกิจ"],
        ["n", "องค์กรไม่แสวงหาผลกำไร"],
      ]),
      f("salary_start", "เงินเดือนเริ่มต้น", "number"),
      f("skill_required", "ทักษะที่จำเป็น", "textarea"),
    ],
  },
  intents: {
    title: "จัดการหมวดหมู่คำถาม (Intent)",
    single: "หมวดหมู่คำถาม",
    columns: ["intent_name", "action_type", "is_active"],
    fields: [
      f("intent_name", "ชื่อหมวดหมู่", "text", true),
      f("description", "รายละเอียด", "textarea"),
      f("prompt_context", "คำสำคัญ (คั่นด้วยเครื่องหมาย ,)", "textarea"),
      f("action_type", "รูปแบบคำตอบ", "select", true, [
        ["rag", "ค้นหาข้อมูล (RAG)"],
        ["rule_based", "คำตอบที่กำหนดไว้"],
      ]),
      f("static_response", "คำตอบที่กำหนดไว้", "textarea"),
      f("is_active", "เปิดใช้งาน", "checkbox"),
    ],
  },
};
export async function api(path: string, method = "GET", body?: unknown) {
  const r = await fetch("/api" + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const raw = await r.text();
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    throw new Error("ระบบเชื่อมต่อขัดข้องหรือใช้เวลาตอบกลับนาน กรุณารีเฟรชเพื่อตรวจสอบข้อมูลก่อนลองอีกครั้ง");
  }
  if (!r.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "ไม่สามารถดำเนินการได้ กรุณาตรวจสอบข้อมูล",
    );
  return data;
}
