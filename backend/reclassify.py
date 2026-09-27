"""Transactional, precondition-checked data reclassification; no commit inside."""
from sqlalchemy import select,delete
from .db import MODELS,Document,Chunk,Chat

def equal(actual,expected):
    return actual==expected or (actual is not None and str(actual)==expected)

def validate(db,plan,lock=False):
    for item in plan['updates']+plan['retire']:
        row=db.get(MODELS[item['table']],item['id'],with_for_update=lock,populate_existing=lock)
        if row is None or any(not equal(getattr(row,k),v) for k,v in item['before'].items()):
            raise ValueError('Record changed since review: '+item['table']+'/'+str(item['id']))
    for item in plan['retire']:
        table,id=item['replacement']
        if not db.get(MODELS[table],id):raise ValueError('Missing replacement')

def apply(db,plan,sync):
    validate(db,plan,lock=True)
    mapping={f"/records/{i['table']}/{i['id']}":f"/records/{i['replacement'][0]}/{i['replacement'][1]}" for i in plan['retire']}
    for item in plan['updates']:
        row=db.get(MODELS[item['table']],item['id'])
        for k,v in item['after'].items():setattr(row,k,v)
        sync(item['table'],row,db)
    # Keep citation positions and historical answer text; only relocate links.
    for chat in db.scalars(select(Chat).where(Chat.sources.is_not(None))):
        if any(s.get('url') in mapping for s in chat.sources or []):
            chat.sources=[{**s,'url':mapping[s['url']]} if s.get('url') in mapping else s for s in chat.sources]
    for item in plan['retire']:
        ids=list(db.scalars(select(Document.id).where(Document.record_type==item['table'],Document.record_id==item['id'])))
        if ids:db.execute(delete(Chunk).where(Chunk.document_id.in_(ids)))
        db.execute(delete(Document).where(Document.id.in_(ids)))
        db.delete(db.get(MODELS[item['table']],item['id']))
    db.flush()
