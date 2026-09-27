"""News recency uses the managed feed unless publication order is requested."""
import re
from datetime import datetime, timezone, timedelta

LATEST = ('ล่าสุด', 'ใหม่สุด', 'ใหม่ที่สุด', 'เพิ่งเพิ่ม', 'เพิ่มใหม่')
BANGKOK = timezone(timedelta(hours=7))

def recency_mode(q):
    if not any(word in q for word in LATEST):
        return None
    return 'published' if any(word in q for word in ('เผยแพร่', 'โพสต์', 'บนเว็บ', 'หน้าเว็บ')) else 'added'

def timestamp(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

def added_news(rows):
    # Never infer timestamps from record IDs; IDs only break equal timestamps.
    valid = [(timestamp(getattr(row, 'created_at', None)), row) for row in rows]
    valid = [(when, row) for when, row in valid if when is not None]
    return [max(valid, key=lambda item: (item[0], item[1].id))[1]] if valid else []

def latest_answer(q, sources):
    # Specific event details still go through grounded generation, not a headline.
    if recency_mode(q) != 'added' or any(word in q for word in
        ('ที่ไหน', 'วันไหน', 'เมื่อไหร่', 'ใครบ้าง', 'มีใคร', 'ผู้ดูแล', 'กี่คน', 'สมัคร', 'รายละเอียด', 'เอกสาร')):
        return None
    if not sources or not all(s['text'].startswith('ข่าวที่เพิ่มล่าสุดในระบบ\n') for s in sources):
        return None
    lines = ['ข่าวที่เพิ่มล่าสุดในระบบคือ:']
    for i, item in enumerate(sources, 1):
        # Date is supplied by retrieval, separately from event/publication dates.
        added = item['text'].split('\n', 2)[1]
        lines.append(f"{item['title']} [{i}]\n{added}")
    return '\n\n'.join(lines), True
