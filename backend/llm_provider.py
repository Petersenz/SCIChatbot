"""Generation-only adapter. Retrieval, scope and evidence do not depend on provider."""
import os
from types import SimpleNamespace
import httpx

class ProviderError(RuntimeError):
    def __init__(self, code, reason='provider_error'):
        super().__init__(reason)
        self.code = code

def identity():
    provider = os.environ.get('LLM_PROVIDER','gemini').lower()
    if provider not in ('gemini','groq'):
        raise ValueError('unsupported_provider')
    model = os.environ.get('GROQ_MODEL','openai/gpt-oss-120b') if provider == 'groq' else os.environ.get('GEMINI_MODEL','')
    return provider, model

class GroqClient:
    def __init__(self):
        self.models = self
        self.client = httpx.Client(timeout=20)
    def close(self): self.client.close()
    def generate_content(self, *, model, contents, config):
        response = self.client.post('https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization':'Bearer '+os.environ['GROQ_API_KEY']},
            json={'model':model, 'messages':[
                {'role':'system','content':config.system_instruction},
                {'role':'user','content':contents}],
                'temperature':config.temperature,'max_completion_tokens':1600,
                'reasoning_effort':'low'})
        if response.status_code != 200:
            # No credential, prompt or raw response in exceptions/logs.
            raise ProviderError(response.status_code)
        result = response.json()['choices'][0]
        if result.get('finish_reason') != 'stop':
            raise ProviderError(502,'incomplete_output')
        body = result['message'].get('content')
        if not body:
            raise ProviderError(502,'empty_output')
        return SimpleNamespace(text=body)
