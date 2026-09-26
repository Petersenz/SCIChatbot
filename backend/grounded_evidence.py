"""Provider-independent evidence preparation. Never infer missing table columns."""
import re
from .query_understanding import TERM, STUDY, whole_curriculum
from .response_style import overview_style

VERSION = 'grounded-evidence-v1'
COLUMNS = ('หน่วยกิต', 'ชั่วโมงทฤษฎี', 'ชั่วโมงปฏิบัติ', 'ชั่วโมงศึกษาด้วยตนเอง')
ROW = re.compile(r'^([A-Z]{2,8}\d{3,8})\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
TOTAL = re.compile(r'^รวม\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')

def plan_table(content):
    # Only the known explicit four-column layout qualifies; no guesses for OCR,
    # missing headings, multiple semesters, or inconsistent totals.
    if not re.search(r'หน่วยกิต\s*ทฤษฎี\s*ปฏิบัติ\s*ศึกษาด้วยตนเอง', content):
        return None
    headings = set(re.findall(r'ปีที่\s*(\d)\s*/\s*ภาคการศึกษาที่\s*(\d)', content))
    if len(headings) != 1:
        return None
    rows, totals = [], []
    for line in content.splitlines():
        row = ROW.fullmatch(line.strip())
        total = TOTAL.fullmatch(line.strip())
        if row:
            rows.append((row[1], row[2], tuple(map(int, row.groups()[2:]))))
        if total:
            totals.append(tuple(map(int, total.groups())))
    if not rows or len(totals) != 1 or len({r[0] for r in rows}) != len(rows):
        return None
    if tuple(sum(r[2][i] for r in rows) for i in range(4)) != totals[0]:
        return None
    return {'year_term':next(iter(headings)), 'rows':rows, 'total':totals[0]}

def prepare_sources(sources):
    result = []
    for source in sources:
        item = dict(source)
        table = plan_table(item['text'])
        if table:
            lines = []
            for line in item['text'].splitlines():
                row, total = ROW.fullmatch(line.strip()), TOTAL.fullmatch(line.strip())
                if row:
                    lines.append(f'{row[1]} {row[2]} | ' + ' | '.join(f'{label}={value}' for label,value in zip(COLUMNS,row.groups()[2:])))
                elif total:
                    lines.append('รวมตามตาราง | ' + ' | '.join(f'{label}={value}' for label,value in zip(COLUMNS,total.groups())))
                else:
                    lines.append(line)
            item['text'] = '\n'.join(lines)
        result.append(item)
    return result

def exact_answer(question, sources):
    """Return grounded display text only when the requested facts are unambiguous.

    This path is shared across providers; factual values come from current
    evidence, never fixed curriculum IDs or hard-coded totals.
    """
    if len(sources) != 1:
        return None
    source = sources[0]
    content = source['text']
    if overview_style(question) and content.startswith('ข้อมูลจากหน้าแนะนำสาขาวิชา:'):
        # An overview may select/format the existing managed description; it
        # must not invent careers/courses from the degree name.
        body = content.removeprefix('ข้อมูลจากหน้าแนะนำสาขาวิชา:').strip()
        body = re.split(r'\s+ไม่พบ', body, maxsplit=1)[0]
        body = re.sub(r'\s+(?=ภาคปกติ|แผนรับ|ผู้สมัคร|สิทธิผู้สมัคร|หน้าเว็บระบุ)', '\n\n', body)
        return body + ' [1]', True
    if 'หน่วยกิต' not in question or any(w in question for w in ['รายวิชา','วิชาอะไร','อะไรบ้าง','ค่าเทอม','อาชีพ','เปรียบเทียบ']):
        return None
    if whole_curriculum(question) and 'ตามข้อมูลที่เจ้าหน้าที่บันทึก ไม่ใช่หน่วยกิตรายเทอม' in content:
        match = re.search(r'หน่วยกิตรวมตลอดหลักสูตร\s+(\d+)\s+หน่วยกิต', content)
        if match:
            # Preserve the stored year label, without declaring a plan year to
            # be a curriculum revision year.
            heading = content.split(' หน่วยกิตรวมตลอดหลักสูตร',1)[0]
            return f'{heading} รวมตลอดหลักสูตร {match[1]} หน่วยกิต [1]', True
    study, term = re.search(STUDY, question), re.search(TERM, question)
    if not study or not term:
        return None
    table = plan_table(content)
    if table and table['year_term'] == (study[1],term[1]):
        return f'{source["title"]} ตามแผนการเรียนที่อ้างอิง ปีที่ {study[1]} ภาคการศึกษาที่ {term[1]} รวม {table["total"][0]} หน่วยกิต [1]', True
    if re.search(r'หน่วยกิต\s*ทฤษฎี\s*ปฏิบัติ', content):
        return 'ยังยืนยันยอดหน่วยกิตจากตารางนี้ไม่ได้ กรุณาตรวจสอบเอกสารต้นฉบับที่แนบครับ [1]', False
    return None
