from types import SimpleNamespace
from backend import rag

def test_same_chunk_count_does_not_hide_changed_content(monkeypatch):
    class DB:
        def flush(self): pass
        def scalar(self, query): return 1
        def execute(self, query, values=None):
            if values is not None: self.writes.extend(values)
            return []
        writes=[]
    db=DB();doc=SimpleNamespace(id=1,content='unchanged PDF',sha256=None)
    calls=[]
    monkeypatch.setattr(rag,'embed',lambda texts: calls.extend(texts) or [[0.0]*768 for _ in texts])
    monkeypatch.setattr(rag,'split_text',lambda text:['old context'])
    rag.index_document(db,doc)
    rag.index_document(db,doc)
    assert calls==['old context']
    monkeypatch.setattr(rag,'split_text',lambda text:['new context'])
    rag.index_document(db,doc)
    assert calls==['old context','new context']
    assert db.writes[-1]['content']=='new context'
