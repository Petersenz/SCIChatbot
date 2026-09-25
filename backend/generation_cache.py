"""Bounded process-local cache. Never skip retrieval or persist user prompts."""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import threading
import time

_entries = OrderedDict()
_lock = threading.Lock()
TTL = 300
LIMIT = 128


def key_for(prompt, sources, model):
    # Include every retrieved source, including uncited candidates: edited/deleted
    # evidence changes this key before any cached answer can be returned.
    value = json.dumps([prompt, sources, model, time.strftime('%Y-%m-%d')],
                       ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(value.encode()).hexdigest()


def get(key):
    with _lock:
        entry = _entries.get(key)
        if not entry:
            return None
        expires, value = entry
        if time.monotonic() >= expires:
            del _entries[key]
            return None
        _entries.move_to_end(key)
        return deepcopy(value)


def put(key, value):
    with _lock:
        _entries[key] = (time.monotonic() + TTL, deepcopy(value))
        _entries.move_to_end(key)
        while len(_entries) > LIMIT:
            _entries.popitem(last=False)


def clear():
    with _lock:
        _entries.clear()
