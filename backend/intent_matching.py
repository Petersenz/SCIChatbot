"""Optional semantic fallback for short static intents, never factual retrieval.

Similarity is not a probability. Thresholds are conservative and validated
against positive/negative utterances; uncertain matches return None.
"""
from math import sqrt
import os
import threading

_lock = threading.Lock()
_vectors = {}
MAX_SAMPLES = 128
MIN_SCORE = 0.90
MIN_MARGIN = 0.08


def clear_cache():
    with _lock:
        _vectors.clear()


def semantic_static_intent(question, intents, encode, route=None):
    if route is not None or not question.strip() or len(question) > 80:
        return None
    eligible = [i for i in intents if i.is_active and i.action_type == 'rule_based' and i.static_response]
    samples = [(i, phrase.strip()) for i in eligible for phrase in (i.prompt_context or '').split(',')
               if 1 < len(phrase.strip()) <= 80]
    if not samples or len(samples) > MAX_SAMPLES:
        return None
    phrases = tuple(phrase for _, phrase in samples)
    key = (os.environ.get('EMBEDDING_MODEL', ''), phrases)
    with _lock:
        cached = _vectors.get(key)
    if cached is None:
        cached = encode(list(phrases))
        with _lock:
            # Cache only configured examples, never personal user utterances.
            if len(_vectors) >= 8:
                _vectors.pop(next(iter(_vectors)))
            _vectors[key] = cached
    vector = encode([question])[0]
    def cosine(other):
        norm = sqrt(sum(x*x for x in vector) * sum(x*x for x in other))
        return sum(a*b for a, b in zip(vector, other)) / norm if norm else 0
    ranked = {}
    for (intent, _), other in zip(samples, cached):
        ranked[intent.id] = (max(ranked.get(intent.id, (0, intent))[0], cosine(other)), intent)
    scores = sorted(ranked.values(), key=lambda item: item[0], reverse=True)
    if not scores or scores[0][0] < MIN_SCORE:
        return None
    if len(scores) > 1 and scores[0][0] - scores[1][0] < MIN_MARGIN:
        return None
    return scores[0][1], scores[0][0]
