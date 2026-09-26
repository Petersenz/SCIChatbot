from backend.grounded_evidence import plan_table, prepare_sources, exact_answer

TEXT='''ปีที่ 1 / ภาคการศึกษาที่ 1
หน่วยกิต ทฤษฎีปฏิบัติศึกษาด้วยตนเอง
SCCS1001 วิชาหนึ่ง 3 2 2 5
SCCS1002 วิชาสอง 3 3 0 6
รวม 6 5 2 11'''
def sources(t=TEXT):
    return [dict(title='หลักสูตรทดสอบ',url='/records/curricula/9',text=t)]

def test_table_column_values_are_not_interchangeable():
    assert plan_table(TEXT)['total']==(6,5,2,11)
    result=prepare_sources(sources())[0]['text']
    assert 'หน่วยกิต=6 | ชั่วโมงทฤษฎี=5 | ชั่วโมงปฏิบัติ=2 | ชั่วโมงศึกษาด้วยตนเอง=11' in result
    assert 'รวม 6 5 2 11' not in result
    body,ok=exact_answer('ปี 1 เทอม 1 เรียนกี่หน่วยกิต',sources())
    assert ok and 'รวม 6 หน่วยกิต' in body

def test_conflicting_or_incomplete_table_fails_closed():
    for bad in [TEXT.replace('รวม 6','รวม 7'),TEXT+'\nปีที่ 2 / ภาคการศึกษาที่ 1',TEXT.replace('SCCS1002 วิชาสอง 3 3 0 6',''),TEXT.replace('หน่วยกิต ทฤษฎีปฏิบัติศึกษาด้วยตนเอง','ข้อมูล')]:
        assert plan_table(bad) is None
    body,ok=exact_answer('ปี 1 เทอม 1 กี่หน่วยกิต',sources(TEXT.replace('รวม 6','รวม 7')))
    assert not ok and 'ยังยืนยัน' in body

def test_not_fixed_to_specific_curriculum_or_values():
    t=TEXT.replace('SCCS1001 วิชาหนึ่ง 3 2 2 5','SCCS1001 วิชาหนึ่ง 4 2 2 5').replace('รวม 6','รวม 7')
    assert 'รวม 7 หน่วยกิต' in exact_answer('ปี 1 เทอม 1 กี่หน่วยกิต',sources(t))[0]
    assert exact_answer('ปี 1 เทอม 1 เรียนวิชาอะไรบ้าง',sources()) is None
    assert exact_answer('ปี 1 เทอม 1 กี่หน่วยกิต',sources()+sources()) is None

def test_introduction_contains_only_stored_facts():
    content='ข้อมูลจากหน้าแนะนำสาขาวิชา: วิทยาศาสตรบัณฑิต ปีหลักสูตร 2568 แผนรับ 30 คน ผู้สมัคร ม.6 สิทธิผู้สมัคร กยศ. หน้าเว็บระบุค่าธรรมเนียม 8,000 บาท แต่ไม่ได้ระบุว่าเป็นต่อภาคเรียน ไม่พบไฟล์หลักสูตร'
    body,ok=exact_answer('อยากทราบเกี่ยวกับ สาขาวิทย์คอมครับ',sources(content))
    assert ok and 'กยศ.' in body and 'ไม่ได้ระบุว่าเป็นต่อภาคเรียน' in body
    for unsupported in ['ต่อปี','ล่าสุด','นักพัฒนา','ปัญญาประดิษฐ์','ไม่พบไฟล์']:
        assert unsupported not in body

def test_total_credit_scope_is_not_semester_scope():
    content='วิทยาการคอมพิวเตอร์ ปีตามรายการหลักสูตร 2570 หน่วยกิตรวมตลอดหลักสูตร 123 หน่วยกิต ตามข้อมูลที่เจ้าหน้าที่บันทึก ไม่ใช่หน่วยกิตรายเทอม'
    assert '123 หน่วยกิต' in exact_answer('ทั้งหลักสูตรมีกี่หน่วยกิต',sources(content))[0]
    assert exact_answer('ปี 1 เทอม 1 กี่หน่วยกิต',sources(content)) is None
