from types import SimpleNamespace as N
from backend.intent_matching import semantic_static_intent, clear_cache


def intent(id, phrase, active=True):
    return N(id=id, prompt_context=phrase, is_active=active, action_type='rule_based', static_response='คำตอบจากตาราง')


def test_threshold_margin_and_factual_question_bypass():
    clear_cache()
    rows = [intent(1, 'hello'), intent(2, 'bye')]
    vectors = {'hello': [1, 0], 'bye': [0, 1], 'hi': [.99, .01], 'uncertain': [.7, .7]}
    def encode(texts): return [vectors[t] for t in texts]
    assert semantic_static_intent('hi', rows, encode)[0].id == 1
    assert semantic_static_intent('uncertain', rows, encode) is None
    assert semantic_static_intent('hi', rows, encode, route='tuition') is None
    assert semantic_static_intent('hi', [intent(1, 'hello', False)], encode) is None
    clear_cache()
    assert semantic_static_intent('hi', [intent(1, 'hello'), intent(2, 'hello')], encode) is None


def test_cache_is_invalidated_by_examples_and_does_not_cache_response():
    clear_cache()
    row = intent(1, 'hello')
    calls = []
    def encode(texts):
        calls.append(texts)
        return [[1, 0] for _ in texts]
    assert semantic_static_intent('hi', [row], encode)[0].static_response == 'คำตอบจากตาราง'
    row.static_response = 'แก้คำตอบแล้ว'
    assert semantic_static_intent('hi', [row], encode)[0].static_response == 'แก้คำตอบแล้ว'
    assert calls.count(['hello']) == 1
    row.prompt_context = 'greetings'
    semantic_static_intent('hi', [row], encode)
    assert ['greetings'] in calls


def test_excessive_samples_and_long_queries_do_not_run_embedding():
    def forbidden(*args): raise AssertionError('should bypass')
    assert semantic_static_intent('x'*81, [intent(1, 'hello')], forbidden) is None
    assert semantic_static_intent('hi', [intent(1, ','.join('word'+str(i) for i in range(129)))], forbidden) is None
