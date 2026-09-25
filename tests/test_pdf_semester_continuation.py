from backend.text_processing import split_evidence

def test_semester_continues_across_pages_and_changes_on_next_heading():
    text='[หน้า 3]\nปีที่ 4 / ภาคการศึกษาที่ 1\n[หน้า 4]\nSCCS4105 ฝึกประสบการณ์ 6 หน่วยกิต\nรวม 6\nปีที่ 4 / ภาคการศึกษาที่ 2\nNEXT วิชาอื่น\n[หน้า 5]\nSCCS4106 TAIL วิชาต่อ\n[หน้า 6]\nภาคผนวก\nข้อความอื่น'
    chunks=split_evidence(text,120)
    internship=next(c for c in chunks if 'SCCS4105' in c)
    assert '[หน้า 4]' in internship
    assert 'ปีที่ 4 / ภาคการศึกษาที่ 1' in internship
    later=next(c for c in chunks if 'TAIL' in c)
    assert 'ภาคการศึกษาที่ 2' in later and 'ภาคการศึกษาที่ 1' not in later
    assert 'ภาคการศึกษาที่' not in next(c for c in chunks if 'ภาคผนวก' in c)
    assert all('ปีที่' not in c for c in split_evidence('[หน้า 1]\nเอกสารทั่วไป\n[หน้า 2]\nข้อความ'))
