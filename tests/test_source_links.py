from types import SimpleNamespace
from backend.source_links import decorate_sources, official_url

def test_official_hostname_is_verified_not_substring():
    assert official_url('https://sci.pcru.ac.th/news/39')
    for value in ['https://pcru.ac.th.evil.test/','javascript:alert(1)','//sci.pcru.ac.th/','https://user@sci.pcru.ac.th/']:
        assert official_url(value) is None

def test_old_and_new_sources_get_current_link_without_mutating_history():
    class DB:
        calls=0
        def get(self,*args):
            self.calls+=1
            return SimpleNamespace(source_url='https://sci.pcru.ac.th/official-news',cover_image='/api/uploads/a.jpg')
    db=DB();cache={};source={'url':'/records/news/39','title':'ข่าว','text':'หลักฐาน','external_url':'https://bad.test'}
    for _ in range(2):
        result=decorate_sources(db,[source],cache)[0]
        assert result['external_url']=='https://sci.pcru.ac.th/official-news'
        assert result['url']==source['url'] and result['text']==source['text']
    assert db.calls==1 and source['external_url']=='https://bad.test'

def test_missing_official_source_keeps_internal_and_uploaded_sources():
    class DB:
        def get(self,*args): return SimpleNamespace(source_url='',file_url='/api/uploads/a.pdf')
    result=decorate_sources(DB(),[{'url':'/records/curricula/24'}])[0]
    assert result['external_url'] is None and result['url']=='/records/curricula/24'
    assert decorate_sources(DB(),[{'url':'https://sci.pcru.ac.th/file.pdf'}])[0]['url'].endswith('file.pdf')
