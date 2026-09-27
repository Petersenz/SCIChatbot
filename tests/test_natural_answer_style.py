import pytest
from backend.news_recency import latest_answer
from backend.career_scope import career_answer
from backend.response_style import polite_answer,RESPONSE_STYLE


def test_latest_omits_storage_metadata_not_article_title_or_citation():
 sources=[dict(title='นักศึกษาผ่านคัดเลือกโครงการ Example Award',text='ข่าวที่เพิ่มล่าสุดในระบบ\nวันที่เพิ่มข้อมูล: 27/09/2569 (ไม่ใช่วันเผยแพร่หรือวันจัดกิจกรรม)\nจัดกิจกรรมวันที่ 14 มิถุนายน 2569')]
 answer,ok=latest_answer('ข่าวล่าสุดคือข่าวอะไร',sources)
 assert ok and answer==sources[0]['title']+' [1]'
 assert latest_answer('ข่าวล่าสุดเพิ่มวันที่เท่าไหร่',sources) is None
 assert latest_answer('ข่าวล่าสุดจัดวันไหน',sources) is None

@pytest.mark.parametrize('q',['เงินเดือนประมาณเท่าไหร่','ทักษะที่จำเป็นมีอะไรบ้าง'])
def test_career_natural_scope_and_qualifiers(q):
 sources=[dict(title='นักพัฒนาเว็บ',career_fact=dict(major='วิทยาการคอมพิวเตอร์',salary=28000,skills='Python, SQL',description='ระดับประสบการณ์: 3–5 ปี\nวิธีประมาณ: เทียบฐานตำแหน่งใกล้เคียง'))]
 answer,ok=career_answer(q,sources)
 assert ok and 'วิทยาการคอมพิวเตอร์' in answer and '[1]' in answer
 assert 'เชื่อมโยง' not in answer and 'ในระบบ' not in answer and 'ที่บันทึก' not in answer
 if 'เงินเดือน' in q:assert '28,000' in answer and '3–5 ปี' in answer and 'เทียบฐานตำแหน่งใกล้เคียง' in answer
 else:assert 'Python, SQL' in answer

@pytest.mark.parametrize('body',[
 'หลักสูตรปีรับเข้า 2570 รวม 121 หน่วยกิต [1]',
 'ค่าใช้จ่าย 8,000 บาท ไม่ระบุว่าต่อภาคเรียน [1]',
 'ทุนนี้ต้องยื่นเอกสารภายในวันที่ 30 กันยายน 2569 [1]',
 'ติดต่อสำนักงาน เวลา 08:30–16:30 น. [1]',
 'สมัครเรียนต้องใช้สำเนาบัตรประชาชน [1]',
 'อาจารย์ผู้รับผิดชอบคืออาจารย์ตัวอย่าง [1]',
 'กิจกรรมจัดที่ห้องประชุม 1 ชั้น 2 [1]',
])
def test_shared_tone_preserves_qualifications_and_facts(body):
 result=polite_answer(body)
 assert result.replace('ค่ะ','')==body


def test_policy_avoids_mechanical_prose_without_erasing_uncertainty():
 assert 'ทุกหัวข้อและทุกโมเดล' in RESPONSE_STYLE
 assert 'ไม่รับรองเกินข้อมูล' in RESPONSE_STYLE
 assert 'คงข้อจำกัดที่เปลี่ยนความหมาย' in RESPONSE_STYLE


def test_english_title_particle_spacing():
 assert polite_answer("Google Student Ambassador Thailand [1]")=="Google Student Ambassador Thailand ค่ะ [1]"
