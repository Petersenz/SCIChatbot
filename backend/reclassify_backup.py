"""Scoped backup/restore for the reviewed migration, including index and citations."""
from datetime import datetime
from sqlalchemy import select,delete,DateTime
from .db import MODELS,Document,Chunk,Chat

def values(row):
    return {c.key:(v.tolist() if hasattr(v,'tolist') else str(v) if isinstance(v,datetime) else v) for c in row.__mapper__.column_attrs for v in [getattr(row,c.key)]}

def capture(db,plan):
    pairs={(i['table'],i['id']) for i in plan['updates']+plan['retire']}
    records=[dict(table=t,id=id,values=values(row) if (row:=db.get(MODELS[t],id)) else None) for t,id in sorted(pairs)]
    docs=[d for d in db.scalars(select(Document)) if (d.record_type,d.record_id) in pairs]
    ids=[d.id for d in docs]
    mapping={f"/records/{i['table']}/{i['id']}" for i in plan['retire']}
    chats=[dict(id=c.id,sources=c.sources) for c in db.scalars(select(Chat)) if any(s.get('url') in mapping for s in c.sources or [])]
    return dict(records=records,documents=[values(d) for d in docs],chunks=[values(c) for c in db.scalars(select(Chunk).where(Chunk.document_id.in_(ids)))],chats=chats)

def restore_values(model,vals):
    result=dict(vals)
    for c in model.__mapper__.column_attrs:
        if isinstance(c.columns[0].type,DateTime) and isinstance(result.get(c.key),str):result[c.key]=datetime.fromisoformat(result[c.key])
    return result

def restore(db,backup):
    pairs={(r['table'],r['id']) for r in backup['records']}
    ids=[d.id for d in db.scalars(select(Document)) if (d.record_type,d.record_id) in pairs]
    db.execute(delete(Chunk).where(Chunk.document_id.in_(ids)));db.execute(delete(Document).where(Document.id.in_(ids)))
    for r in backup['records']:
        model=MODELS[r['table']];row=db.get(model,r['id'])
        if r['values'] is None:
            if row:db.delete(row)
        elif row:
            for k,v in restore_values(model,r['values']).items():setattr(row,k,v)
        else:db.add(model(**restore_values(model,r['values'])))
    db.flush()
    for d in backup['documents']:db.add(Document(**restore_values(Document,d)))
    db.flush()
    for c in backup['chunks']:db.add(Chunk(**c))
    for c in backup['chats']:
        row=db.get(Chat,c['id'])
        if row:row.sources=c['sources']
    db.flush()
