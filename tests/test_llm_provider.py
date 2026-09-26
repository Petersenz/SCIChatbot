from types import SimpleNamespace
import httpx
import pytest
from backend.llm_provider import GroqClient, ProviderError, identity

def test_provider_identity_is_explicit(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER','groq')
    monkeypatch.delenv('GROQ_MODEL',raising=False)
    assert identity()==('groq','openai/gpt-oss-120b')
    monkeypatch.setenv('LLM_PROVIDER','invalid')
    with pytest.raises(ValueError): identity()

@pytest.mark.parametrize('status,finish,expected',[(200,'stop',None),(200,'length',502),(429,None,429),(401,None,401),(503,None,503)])
def test_transport_preserves_prompt_and_rejects_failure(monkeypatch,status,finish,expected):
    monkeypatch.setenv('GROQ_API_KEY','unit-placeholder')
    sent=[]
    def handle(request):
        import json
        sent.append(json.loads(request.content))
        return httpx.Response(status,json={'choices':[{'finish_reason':finish,'message':{'content':'หลักฐาน [1]'}}]})
    client=GroqClient();client.client.close()
    client.client=httpx.Client(transport=httpx.MockTransport(handle))
    config=SimpleNamespace(system_instruction='same rules',temperature=0.15)
    try:
        if expected:
            with pytest.raises(ProviderError) as err:
                client.generate_content(model='test',contents='same evidence',config=config)
            assert err.value.code==expected and 'unit-placeholder' not in str(err.value)
        else:
            assert client.generate_content(model='test',contents='same evidence',config=config).text=='หลักฐาน [1]'
        assert sent[0]['messages'][1]['content']=='same evidence'
        assert sent[0]['messages'][0]['content']=='same rules'
    finally: client.close()
