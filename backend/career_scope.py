"""Career identity matching and factual answers, independent of LLM provider.

Aliases identify roles, never prove a relationship to a major. Membership is
always established separately by CurriculumCareer.
"""
import re

ROLE_ALIASES = (
    (('ทำเว็บ', 'พัฒนาเว็บ', 'web developer'), ('พัฒนาเว็บ',)),
    (('ดูแลเว็บ', 'web administrator'), ('ดูแลเว็บไซต์',)),
    (('dba', 'ผู้ดูแลฐานข้อมูล', 'database administrator'), ('ผู้ดูแลฐานข้อมูล',)),
    (('สถาปนิกฐานข้อมูล', 'database architect'), ('สถาปนิกฐานข้อมูล',)),
    (('ui/ux', 'ux/ui', 'ออกแบบหน้าจอ'), ('ส่วนติดต่อ',)),
    (('ออกแบบเกม', 'game designer'), ('ออกแบบเกม',)),
    (('data scientist', 'นักวิทยาศาสตร์ข้อมูล'), ('นักวิทยาศาสตร์ข้อมูล',)),
    (('ทดสอบซอฟต์แวร์', 'software qa'), ('ทดสอบ',)),
)


def contains(value, phrase):
    if re.fullmatch(r'[a-zA-Z /]+', phrase):
        return bool(re.search(r'(?<![a-zA-Z])' + re.escape(phrase) + r'(?![a-zA-Z])', value, re.I))
    return phrase in value


def career_names(question, titles):
    q = question.lower()
    exact = [title for title in titles if title.lower() in q]
    if exact:
        return exact
    needles = [needle for aliases, names in ROLE_ALIASES
               if any(contains(q, alias) for alias in aliases) for needle in names]
    return [title for title in titles if any(needle in title.lower() for needle in needles)]


def salary_question(q):
    return any(w in q for w in ('เงินเดือน', 'รายได้', 'ค่าตอบแทน'))


def career_answer(q, sources):
    """Only answer simple recorded salary/skill questions without generation.

Complex comparisons or recommendations remain with the grounded LLM path.
"""
    if not sources or not all('career_fact' in s for s in sources):
        return None
    if any(w in q for w in ('เปรียบเทียบ', 'ทำไม', 'แนะนำ', 'คุ้ม', 'เหมาะ', 'มากกว่า')):
        return None
    salary = salary_question(q)
    skills = 'ทักษะ' in q
    if not (salary or skills):
        return None
    scope = sources[0]['career_fact']['major']
    lines = [f'สำหรับสาขา{scope} ข้อมูลอาชีพที่เชื่อมโยงไว้ในระบบมีดังนี้ค่ะ:' if scope
             else 'ข้อมูลของอาชีพที่คุณระบุในระบบมีดังนี้ค่ะ:']
    supported = False
    for i, source in enumerate(sources, 1):
        fact = source['career_fact']
        parts = []
        if salary:
            amount = fact['salary']
            if amount is None:
                parts.append('ยังไม่มีข้อมูลเงินเดือนในรายการนี้')
            elif any(w in q for w in ('จบใหม่', 'ไม่มีประสบการณ์')) and ('ไม่ควรใช้เป็นอัตราเริ่มต้นสำหรับผู้จบใหม่' in fact['description'] or 'ไม่ใช่สถิติเด็กจบใหม่' in fact['description']):
                parts.append('ข้อมูลเงินเดือนที่มีเป็นฐานของผู้มีประสบการณ์ จึงยังยืนยันเงินเดือนสำหรับผู้จบใหม่ไม่ได้')
            else:
                supported = True
                parts.append(f'ค่าประมาณตามข้อมูลที่บันทึก {amount:,.0f} บาท/เดือน')
                qualifiers = [line.strip() for line in fact['description'].splitlines()
                              if line.startswith(('ระดับประสบการณ์', 'วิธีประมาณ:', 'ฐานเปรียบเทียบ:'))]
                parts.extend(qualifiers)
                if not qualifiers:
                    parts.append('รายการนี้ไม่ได้ระบุระดับประสบการณ์ที่ใช้เป็นฐาน')
        if skills:
            parts.append('ทักษะ: ' + (fact['skills'] or 'ยังไม่มีข้อมูลทักษะในรายการนี้'))
            supported |= bool(fact['skills'])
        lines.append(f'• {source["title"]}: ' + ' — '.join(parts) + f' [{i}]')
    if salary:
        lines.append('ตัวเลขนี้ไม่ใช่รายได้ที่รับรอง และไม่ควรถือว่าทุกรายการเป็นอัตราสำหรับผู้จบใหม่')
    return '\n\n'.join(lines), supported
