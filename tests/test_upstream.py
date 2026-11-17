import base64,json
import pytest
import pymupdf
from fastapi.testclient import TestClient
from app.main import app
from app import llm

@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'})
        yield c

def make_pdf(texts):
    doc=pymupdf.open()
    for text in texts:
        p=doc.new_page();p.insert_text((72,72),text)
    raw=doc.tobytes();doc.close();return raw

def upload(c,name,raw):return c.post('/api/documents/pdf',json={'name':name,'content_base64':base64.b64encode(raw).decode()})
def stream(c,**body):
    r=c.post('/api/upstream/stream',json={'question':'资料约定编号是什么？','mode':'demo',**body})
    assert r.status_code==200,r.text
    return [(b.splitlines()[0][7:],json.loads(b.splitlines()[1][6:])) for b in r.text.strip().split('\n\n')]
def contract(events):return next(v for k,v in events if k=='plan')

def test_pdf_page_offsets_duplicate_original_acl(client):
    raw=make_pdf(['ORION policy page one','ORION reference code REF-7319'])
    r=upload(client,'source.pdf',raw);assert r.status_code==201,r.text
    a=r.json();assert a['metadata']['pages']==2
    assert upload(client,'again.pdf',raw).json()['id']==a['id']
    full=client.get('/api/assets/'+a['id']).json()
    assert {c['page'] for c in full['metadata']['chunks']}=={1,2}
    for c in full['metadata']['chunks']:assert full['content'][c['offset']:c['offset']+len(c['text'])]==c['text']
    assert client.get('/api/documents/'+a['id']+'/original').content==raw
    e=stream(client,question='文档 ORION REF-7319 reference',document_ids=[a['id']])
    assert any(v.get('page')==2 for k,v in e if k=='source')
    assert contract(e)['status']=='answered'
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert client.get('/api/documents/'+a['id']+'/original').status_code==404
    assert client.post('/api/upstream/stream',json={'question':'解释文档','mode':'demo','document_ids':[a['id']]}).status_code==404

@pytest.mark.parametrize('name,text',[('blank.pdf',''),('../bad.pdf','hello')])
def test_scan_and_path_rejected(client,name,text):
    assert upload(client,name,make_pdf([text])).status_code==422

def test_clarification_bos_not_connected(client):
    e=stream(client,question='优化 BOS 场景线路状态',session_id='same')
    c=contract(e)
    assert c['status']=='needs_clarification' and c['plan_steps']==[]
    assert c['constraints']['execution_authorized'] is False
    e=stream(client,question='BOS 场景线路状态',scene_ref='teaching-scene',snapshot_ref='teaching-snapshot')
    assert any('尚未接入' in m for m in contract(e)['missing_fields'])

def test_plan_checkpoint_and_no_execution(client):
    a=client.post('/api/assets',json={'name':'plan.csv','kind':'dataset','content':'line_id,active_power_mw,limit_mw\nA,120,100\n'}).json()
    d=client.post('/api/assets',json={'name':'plan.md','kind':'knowledge','content':'线路 CSV 分析计划先读取校验数据，再计算给定功率限值的负载比值，检索说明并生成报告。'}).json()
    before=len(client.get('/api/tasks').json())
    e=stream(client,question='为线路 CSV 分析生成步骤计划',dataset_id=a['id'],document_ids=[d['id']],session_id='plan-session')
    c=contract(e)
    assert c['status']=='ready_for_planner',e
    assert len(c['plan_steps'])==4 and c['scope']['dataset_sha256']==a['metadata']['sha256']
    assert all(s['execution']=='not_executed' for s in c['plan_steps'])
    assert len(client.get('/api/tasks').json())==before and e[-1][0]=='done'
    from app.config import settings
    assert (settings.runtime/'upstream-checkpoints.sqlite3').exists()
    c=contract(stream(client,question='帮我优化一下',session_id='plan-session'))
    assert c['scope']['dataset_ref'] is None and c['status']=='needs_clarification'

def test_document_filter_empty_evidence(client):
    a=client.post('/api/assets',json={'name':'filter.md','kind':'knowledge','content':'violet maintenance'}).json()
    client.post('/api/assets',json={'name':'other.md','kind':'knowledge','content':'ORION policy reference'}).json()
    e=stream(client,question='文档 ORION policy reference',document_ids=[a['id']])
    assert all(v['document_id']==a['id'] for k,v in e if k=='source')
    assert contract(stream(client,question='文档 zzq_nonexistent_779431'))['status']=='needs_evidence'

def test_model_error_no_done(client,monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings,'api_key','test-placeholder-only')
    async def fail(*a,**kw):raise llm.ModelUnavailable('模型不可用')
    monkeypatch.setattr(llm,'completion',fail)
    e=stream(client,question='分析资料',mode='live')
    assert e[-1][0]=='error' and not any(k=='done' for k,v in e)

def test_validator_unknown_tool_and_permission():
    from app.upstream.schemas import TaskContract,PlanStep
    from app.upstream.validators import validate_contract
    c=TaskContract(request_id='teaching',intent_type='analysis',scope={},goal={},created_at='teaching',status='needs_evidence')
    c.plan_steps=[PlanStep(step_id='s1',capability_id='unknown_write',purpose='no')]
    with pytest.raises(ValueError,match='未知能力'):validate_contract(c,set())
    c.plan_steps=[];c.constraints['execution_authorized']=True
    with pytest.raises(ValueError,match='执行'):validate_contract(c,set())

def test_upstream_history_is_durable_and_owner_isolated(client):
    e=stream(client,question='BOS 场景线路状态',session_id='history-test')
    history=client.get('/api/upstream/sessions').json()
    assert any(t['session_id']=='history-test' for t in history)
    assert history[0]['response']['contract']['constraints']['execution_authorized'] is False
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert all(t['session_id']!='history-test' for t in client.get('/api/upstream/sessions').json())
