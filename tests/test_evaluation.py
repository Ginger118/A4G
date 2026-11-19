"""Metric and isolation contracts; mocked hits are not live retrieval evidence."""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import evaluation as e, storage as store
from app.config import settings

A='a'*64;B='b'*64

def case(refs=(A,B)):
    return e.Case(id='test',question='演示问题',rationale='预先定义',references=[e.Reference(title=h[0]+'.md',sha256=h) for h in refs])

def row(id,sha):
    return {'id':id,'metadata':{'original_sha256':sha}}


def test_duplicate_chunks_count_reference_document_once():
    result=e.score_case(case(),[{'document_id':'a','chunk_id':i} for i in range(4)],[row('a',A),row('b',B)])
    assert result['recall']==.5 and result['matched_documents']==1


def test_foreign_and_irrelevant_hits_do_not_count():
    assert e.score_case(case((A,)),[{'document_id':'foreign'}],[row('own',A)])['recall']==0


def test_missing_version_is_unscored_not_zero_or_one():
    c=e.score_case(case(),[{'document_id':'a'}],[row('a',A)])
    assert c['recall'] is None and c['status']=='unavailable'
    good=e.score_case(case((A,)),[{'document_id':'a'}],[row('a',A)])
    assert e.summarize([c,good])['macro_recall']==1
    assert e.summarize([c])['macro_recall'] is None


@pytest.fixture
def prepared(monkeypatch,tmp_path):
    monkeypatch.setattr(settings,'runtime',tmp_path/'runtime');store.init()
    data=e.load_suite().model_dump();data['cases']=[case((A,)).model_dump()]
    path=tmp_path/'suite.json';path.write_text(json.dumps(data));monkeypatch.setattr(e,'SUITE_PATH',path)
    a=store.asset('own','a.md','knowledge','参考文本',{'original_sha256':A,'index_status':'ready'})
    store.asset('foreign','b.md','knowledge','外部文本',{'original_sha256':B,'index_status':'ready'})
    calls=[]
    def search(owner,query,top_k):
        calls.append((owner,query,top_k));return [{'document_id':a['id'],'chunk_id':1,'document':'a.md','text':'参考文本','score':.6}]
    monkeypatch.setattr(e.rag,'search',search)
    monkeypatch.setattr('app.embeddings.embedding_info',lambda:{'model':'explicit-test-double','semantic':False})
    return a,calls


def test_run_uses_full_current_user_scope_and_roundtrip(prepared):
    _,calls=prepared;r=e.evaluate('own')
    assert calls==[('own','演示问题',4)] # No reference document_ids forced into retrieval.
    assert r['summary']['macro_recall']==1 and r['retriever']['corpus_documents']==1
    assert e.snapshot('own')['latest']==r
    assert e.snapshot('foreign')['latest'] is None
    assert e.report_path('own').stat().st_mode & 0o777==0o600


def test_stale_after_corpus_or_suite_changes(prepared):
    e.evaluate('own');assert not e.snapshot('own')['stale']
    store.asset('own','new.md','knowledge','新资料',{'original_sha256':B,'index_status':'ready'})
    assert e.snapshot('own')['stale']
    e.evaluate('own');assert not e.snapshot('own')['stale']
    data=json.loads(e.SUITE_PATH.read_text());data['cases'][0]['question']='修改后的演示问题';e.SUITE_PATH.write_text(json.dumps(data))
    assert e.snapshot('own')['stale']


def test_service_failure_retains_last_complete_result(prepared,monkeypatch):
    r=e.evaluate('own');before=e.report_path('own').read_bytes()
    def failed(*a,**k):raise ValueError('simulated outage')
    monkeypatch.setattr(e.rag,'search',failed)
    with pytest.raises(ValueError):e.evaluate('own')
    assert e.report_path('own').read_bytes()==before


def test_corpus_change_during_run_rejected(prepared,monkeypatch):
    original=e.rag.search
    def changed(*a,**k):
        store.asset('own','midrun.md','knowledge','模拟运行期间新资料',{'original_sha256':B,'index_status':'ready'})
        return original(*a,**k)
    monkeypatch.setattr(e.rag,'search',changed)
    with pytest.raises(e.HTTPException) as exc:e.evaluate('own')
    assert exc.value.status_code==409 and not e.report_path('own').exists()


def test_simultaneous_run_rejected(prepared):
    lock=e.threading.Lock();lock.acquire();e._LOCKS['own']=lock
    try:
        with pytest.raises(e.HTTPException) as exc:e.evaluate('own')
        assert exc.value.status_code==409
    finally:lock.release()


def test_routes_preserve_owner_and_safe_failure(prepared,monkeypatch):
    app=FastAPI();app.include_router(e.build_evaluation_router(lambda:{'id':'own'}))
    with TestClient(app) as c:
        assert c.post('/api/evaluation/demo/run').json()['summary']['macro_recall']==1
        monkeypatch.setattr(e.rag,'search',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('private service response')))
        r=c.post('/api/evaluation/demo/run');assert r.status_code==503
        assert 'private service response' not in r.text
        assert c.get('/api/evaluation/demo').json()['latest']['summary']['macro_recall']==1


def test_actual_app_endpoints_require_login():
    from app.main import app
    with TestClient(app) as c:
        assert c.get('/api/evaluation/demo').status_code==401
        assert c.post('/api/evaluation/demo/run').status_code==401
