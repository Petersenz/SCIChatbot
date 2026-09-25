"""Conservative question normalization within the faculty-advising scope."""
import re
from .text_processing import normalize_text

YEAR = r'(?<!\d)(25\d{2})(?!\d)'
STUDY = r'ปี\s*(?:ที่\s*)?([1-6])(?!\d)'
TERM = r'(?:เทอม|ภาคเรียน|ภาคการศึกษา)\s*(?:ที่\s*)?([1-3])(?!\d)'


def canonical(value):
    value = normalize_text(value).translate(str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789'))
    for word, number in [('หนึ่ง', '1'), ('สอง', '2'), ('สาม', '3'), ('สี่', '4'), ('ห้า', '5'), ('หก', '6')]:
        value = re.sub(r'((?:ปี|เทอม|ภาคเรียน|ภาคการศึกษา)\s*(?:ที่\s*)?)' + word, r'\g<1>' + number, value)
    value = re.sub(r'(?:ค\.ศ\.\s*|ปี\s*)(20\d{2})(?!\d)', lambda m: 'ปี ' + str(int(m.group(1)) + 543), value)
    aliases = [
        (r'วิทย์?คอม(?:พิวเตอร์)?|วิทคอม|คอมพิวเตอร์ไซเอนซ์|(?<![a-zA-Z])computer\s+science(?![a-zA-Z])|(?<![a-zA-Z])cs(?![a-zA-Z])', 'วิทยาการคอมพิวเตอร์'),
        (r'ไอที|(?<![a-zA-Z])it(?![a-zA-Z])', 'เทคโนโลยีสารสนเทศ'),
        (r'(?<!การ)แพทย์แผนไทย', 'การแพทย์แผนไทย'),
        (r'สาธารณสุข(?!ศาสตร์)', 'สาธารณสุขศาสตร์'),
    ]
    for pattern, replacement in aliases:
        value = re.sub(pattern, replacement, value, flags=re.I)
    value = re.sub(r'ก\.?\s*ย\.?\s*ศ\.?', 'กยศ', value)
    return value


def topic(q):
    q = q.lower()
    if any(t in q for t in ['ค่าเทอม', 'ค่าเล่าเรียน', 'ค่าธรรมเนียม', 'ค่าบำรุง']):
        return 'tuition'
    if any(t in q for t in ['ข่าว', 'ประกาศ', 'รับสมัคร', 'สมัครเรียน', 'open house']):
        return 'news'
    if any(t in q for t in ['อาชีพ', 'ทำงาน', 'จบไป', 'เงินเดือน', 'ทักษะ']):
        return 'career'
    if any(t in q for t in ['ติดต่อ', 'ที่อยู่', 'ตั้งอยู่', 'เบอร์โทร', 'โทรศัพท์', 'อีเมล']):
        return 'contact'
    if any(t in q for t in ['ก่อตั้ง', 'ประวัติคณะ']):
        return 'history'
    if any(t in q for t in ['วิสัยทัศน์', 'พันธกิจ']):
        return 'mission'
    return 'curriculum'


def mentioned_majors(q, majors):
    return [m for m in majors if m.major_name_th in q]


def whole_curriculum(q):
    return any(word in q for word in ['ทั้งหลักสูตร', 'ตลอดหลักสูตร', 'รวมทั้งหลักสูตร', 'หลักสูตรทั้งหมด']) or (
        'หน่วยกิต' in q and 'รวม' in q and not re.search(TERM, q) and not re.search(STUDY, q))


def general_topic(q):
    for label, words in [('ทุนการศึกษา', ['ทุน', 'กยศ', 'กู้เรียน', 'กู้ค่าเรียน']),
                         ('บุคลากร', ['บุคลากร', 'อาจารย์']),
                         ('ติดต่อ', ['ติดต่อ', 'เบอร์โทร', 'โทรศัพท์', 'อีเมล']),
                         ('สมัคร', ['ขั้นตอนการสมัคร', 'วิธีสมัคร', 'สมัครยังไง', 'สมัครอย่างไร'])]:
        if any(word in q for word in words):
            return label
    if 'บริการ' in q and 'นักศึกษา' in q:
        return 'บริการนักศึกษา'
    return None


def resolve(q, history, majors):
    state = ''
    for raw in [t.user_query for t in history] + [q]:
        current = canonical(raw)
        named = mentioned_majors(current, majors)
        old_named = mentioned_majors(state, majors)
        general = general_topic(current)
        # Carry the major, not the old semester/year, into a new general topic.
        if general and not named and old_named and not any(x in current for x in ['ทั้งคณะ', 'ของคณะ', 'มหาวิทยาลัย', 'ทุกสาขา']):
            current = old_named[0].major_name_th + ' ' + current
            named = mentioned_majors(current, majors)
        followup = any(t in current for t in ['แล้ว', 'เทอม', 'ภาคเรียน', 'ภาคการศึกษา', 'สาขานี้', 'หลักสูตรนี้', 'หน่วยกิต', 'ทั้งหลักสูตร', 'ตลอดหลักสูตร', 'ค่าเทอม', 'จบไป'])
        same = not named or {m.id for m in named} == {m.id for m in old_named}
        if followup and same and old_named and not general and topic(current) not in ['news', 'contact', 'history', 'mission']:
            if not named:
                current = old_named[0].major_name_th + ' ' + current
            patterns = [YEAR]
            new_year, old_year = re.search(YEAR, current), re.search(YEAR, state)
            changed_year = bool(new_year and old_year and new_year.group(1) != old_year.group(1))
            total_question = whole_curriculum(current) or any(x in current for x in ['รวม', 'ทั้งหมด'])
            if topic(current) == 'curriculum' and not changed_year and not total_question:
                patterns.append(STUDY)
                if 'หน่วยกิต' in current and not any(x in current for x in ['รวม', 'ทั้งหมด', 'ตลอดหลักสูตร']):
                    patterns.append(TERM)
            for pattern in patterns:
                if not re.search(pattern, current):
                    old = re.search(pattern, state)
                    if old:
                        current += ' ' + old.group(0)
        if 'เทอมแรก' in current and not re.search(STUDY, current):
            current += ' ปีที่ 1'
        # Materialize first-term wording so later short credit questions inherit it.
        if 'เทอมแรก' in current:
            current = current.replace('เทอมแรก', 'เทอม 1')
        state = current
    return state


def ambiguity(q, majors):
    if len(set(re.findall(YEAR, q))) > 1:
        return 'ต้องการสอบถามข้อมูลปีไหนก่อนครับ'
    if topic(q) == 'curriculum' and len(set(re.findall(TERM, q))) > 1:
        return 'ต้องการสอบถามภาคเรียนไหนก่อนครับ'
    named = mentioned_majors(q, majors)
    if not named and whole_curriculum(q) and not any(word in q for word in ['แต่ละสาขา', 'ทุกสาขา', 'ทั้งคณะ']):
        return 'ต้องการทราบหน่วยกิตรวมของสาขาไหน และปีหลักสูตรใดครับ'
    if len(named) > 1:
        return 'ต้องการสอบถามสาขาไหนก่อนครับ: ' + ' หรือ '.join(m.major_name_th for m in named)
    if not named:
        for fragment in ['ชีววิทยา', 'คณิตศาสตร์']:
            choices = [m.major_name_th for m in majors if fragment in m.major_name_th]
            if fragment in q and len(choices) > 1:
                return 'หมายถึงสาขาไหนครับ: ' + ' หรือ '.join(choices)
    if topic(q) == 'curriculum' and re.search(TERM, q) and not re.search(STUDY, q):
        return 'ต้องการแผนการเรียนของชั้นปีไหนครับ'
    return None
