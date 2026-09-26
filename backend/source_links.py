"""Resolve citation display links without changing retrieval IDs or stored history."""
import re
from urllib.parse import urlparse
from .db import MODELS

def official_url(value):
    try:
        parsed = urlparse(value or '')
        host = (parsed.hostname or '').lower()
        return value if parsed.scheme in ('http','https') and not parsed.username and (host == 'pcru.ac.th' or host.endswith('.pcru.ac.th')) else None
    except ValueError:
        return None

def decorate_sources(db, sources, cache=None):
    cache = cache if cache is not None else {}
    result=[]
    for source in sources or []:
        item=dict(source)
        # Never trust an old client-provided display override.
        item.pop('external_url',None)
        match=re.fullmatch(r'/records/(news|general|curricula|careers|majors)/(\d+)', source.get('url',''))
        if match:
            entity,identifier=match[1],int(match[2])
            key=(entity,identifier)
            if key not in cache: cache[key]=db.get(MODELS[entity],identifier)
            row=cache[key]
            if row:
                candidates=[getattr(row,'source_url',None)]
                if entity=='curricula': candidates.append(getattr(row,'file_url',None))
                if entity=='majors': candidates.append(getattr(row,'website_url',None))
                item['external_url']=next((url for value in candidates if (url:=official_url(value))),None)
        result.append(item)
    return result
