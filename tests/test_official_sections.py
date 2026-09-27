from backend.grounded_evidence import exact_answer
TEXT='ปรัชญา\n“มีความรู้ คู่คุณธรรม”\nวิสัยทัศน์\nผลิตบัณฑิตที่มีคุณภาพ\nพันธกิจ\n1.บริการวิชาการ\n2.วิจัย\n3.ผลิตบัณฑิต\n4.ทำนุบำรุง\n5.บริหาร'
def src(t=TEXT,url='/records/general/3'):return [dict(title='วิสัยทัศน์และพันธกิจ',text=t,url=url)]
def test_exact_user_question_preserves_sections():
 body,ok=exact_answer('วิสัยทัศน์และพันธกิจ ของคณะคืออะไร',src())
 assert ok and body.count('## ')==2
 for line in TEXT.split('พันธกิจ\n')[1].splitlines():assert line in body
 assert 'ปรัชญา' not in body

def test_philosophy_and_combined():
 assert '“มีความรู้ คู่คุณธรรม”' in exact_answer('ปรัชญาของคณะคืออะไร',src())[0]
 assert exact_answer('ปรัชญา วิสัยทัศน์ พันธกิจ',src())[0].count('## ')==3

def test_ambiguous_missing_and_summary_use_generation():
 for q,s in [('สรุปพันธกิจ',src()),('วิสัยทัศน์',src(TEXT+'\nวิสัยทัศน์\nอื่น')),('ปณิธาน',src()),('พันธกิจ',src(url='/records/news/3'))]:assert exact_answer(q,s) is None
 assert exact_answer('พันธกิจ',src()+src()) is None

def test_current_stored_text_not_fixed_answer():
 assert 'ปรับข้อมูลใหม่' in exact_answer('วิสัยทัศน์',src(TEXT.replace('ผลิตบัณฑิตที่มีคุณภาพ','ปรับข้อมูลใหม่')))[0]

def test_expanded_search_terms_do_not_expand_requested_sections():
 body,ok=exact_answer('ปรัชญา วิสัยทัศน์ พันธกิจ',src(),original_question='ปรัชญาของคณะคืออะไร')
 assert ok and body.count('## ')==1 and '## ปรัชญา' in body
