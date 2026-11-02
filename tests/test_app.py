import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.tools.business import validate_csv, build_registry
from app.agent.contracts import ToolCall, PlanningContext, ToolArguments, ToolSpec
from app.agent.executor import Executor
from app.agent.runtime import run_task
from app import storage as store, rag

CSV='id,date,product,feedback\nT1,2026-11-01,产品 A,水箱漏水\nT2,2026-11-02,产品 B,物流未送达\nT3,2026-11-02,产品 A,退款迟迟未处理\n'

@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'})
        yield c

def test_authentication_and_admin_permissions():
    with TestClient(app) as c:
        assert c.get('/api/assets').status_code==401
        assert c.post('/api/auth/login',json={'username':'demo','password':'wrong'}).status_code==401
        assert c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'}).status_code==200
        assert c.get('/api/admin/summary').status_code==403
        c.post('/api/auth/logout',json={})
        assert c.get('/api/auth/me').status_code==401

def test_csv_validation_and_new_input(client):
    assert client.post('/api/assets',json={'name':'new.csv','kind':'dataset','content':CSV}).status_code==201
    bad=CSV.replace('T2,','T1,')
    assert client.post('/api/assets',json={'name':'bad.csv','kind':'dataset','content':bad}).status_code==422
    assert client.post('/api/assets',json={'name':'../bad.csv','kind':'dataset','content':CSV}).status_code==422
    assert client.post('/api/assets',json={'name':'bad.csv','kind':'dataset','content':'bad,data\n1,2'}).status_code==422
    assert client.post('/api/assets',json={'name':'bad.csv','kind':'dataset','content':CSV.replace('2026-11-01','not-a-date')}).status_code==422

def test_resource_isolation(client):
    a=client.post('/api/assets',json={'name':'private.csv','kind':'dataset','content':CSV}).json()
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert client.get('/api/assets/'+a['id']).status_code==404
    assert client.get('/api/assets/'+a['id']+'/download').status_code==404
    assert client.post('/api/tasks',json={'prompt':'分析报告','dataset_id':a['id'],'mode':'demo'}).status_code==404
    assert all(v['id']!=a['id'] for v in client.get('/api/assets').json())

def test_new_knowledge_and_no_answer(client):
    a=client.post('/api/assets',json={'name':'new-rule.md','kind':'knowledge','content':'紫菀设备特殊保修：序列号 ZY991 的检测周期为 17 个工作日。'}).json()
    result=client.post('/api/knowledge/ask',json={'question':'紫菀 ZY991 检测周期是多少？','mode':'demo'}).json()
    assert any(h['document_id']==a['id'] for h in result['citations'])
    assert '17' in result['answer']
    result=client.post('/api/knowledge/ask',json={'question':'zxqv_nonexistent_token_679','mode':'demo'}).json()
    assert result['citations']==[]
    assert '未找到' in result['answer']

def test_demo_end_to_end_and_trace(client):
    user=client.get('/api/auth/me').json()
    asset=client.post('/api/assets',json={'name':'three-new-records.csv','kind':'dataset','content':CSV}).json()
    task_id=store.uid('test')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,user['id'],'test_session','分析产品 A 的反馈并生成报告','demo','pending',store.dumps({'input_id':asset['id']}),'','',store.now(),store.now()))
    asyncio.run(run_task(task_id,build_registry()))
    task=client.get('/api/tasks/'+task_id).json()
    assert task['status']=='succeeded',task
    assert task['state']['statistics']['total']==2
    assert len(task['state']['statistics']['row_ids'])==2
    assert sum(g['count'] for g in task['state']['statistics']['groups'])==2
    report=client.get('/api/assets/'+task['state']['report_id']).json()
    assert '本地规则演示' in report['content']
    assert '2** 条反馈' in report['content']
    assert len([e for e in task['events'] if e['type']=='tool_completed'])==5
    trace=client.get('/api/tasks/'+task_id+'/trace')
    assert trace.status_code==200
    assert all(json.loads(line) for line in trace.text.splitlines())
    assert 'AGENT_API_KEY' not in trace.text
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert client.get('/api/tasks/'+task_id).status_code==404
    assert client.get('/api/tasks/'+task_id+'/trace').status_code==404

def test_executor_invalid_tool_parameters_and_timeout(client):
    owner=client.get('/api/auth/me').json()['id']
    registry=build_registry();executor=Executor(registry)
    ctx=PlanningContext('test_executor',owner,'test','demo',{},[],registry.available_specs())
    result=asyncio.run(executor.execute(ToolCall(tool_id='unknown',arguments={}),ctx))
    assert not result.success
    result=asyncio.run(executor.execute(ToolCall(tool_id='inspect_dataset',arguments={'wrong':'value'}),ctx))
    assert not result.success and '参数' in result.error
    result=asyncio.run(executor.execute(ToolCall(tool_id='inspect_dataset',arguments={'dataset_id':'outside'}),ctx))
    assert not result.success and '无权' in result.error
    async def slow(args,context):
        await asyncio.sleep(.2)
        return {'ok':True}
    registry.register(ToolSpec('slow','slow','slow',ToolArguments,slow,timeout=.01))
    result=asyncio.run(executor.execute(ToolCall(tool_id='slow'),ctx))
    assert not result.success and '超时' in result.error

def test_invalid_image_rejected(client):
    result=client.post('/api/vision',json={'image_base64':'bm90LWEtcmVhbC1pbWFnZQ=='})
    assert result.status_code==422

def test_model_failure_does_not_become_success(client,monkeypatch):
    from app import llm
    async def broken(*args,**kwargs): raise llm.ModelUnavailable('连接失败测试')
    monkeypatch.setattr(llm,'completion',broken)
    owner=client.get('/api/auth/me').json()['id'];task_id=store.uid('test')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,owner,'test','生成报告','live','pending','{}','','',store.now(),store.now()))
    asyncio.run(run_task(task_id,build_registry()))
    task=client.get('/api/tasks/'+task_id).json()
    assert task['status']=='failed'
    assert not task['state'].get('report_id')

def test_step_limit_stops_infinite_planning(client,monkeypatch):
    from app.agent import runtime
    from app.agent.contracts import PlannerDecision
    class LoopPlanner:
        async def decide(self,context):
            return PlannerDecision(kind='call_tool',calls=[ToolCall(tool_id='search_knowledge',arguments={'query':'售后'})])
    monkeypatch.setitem(runtime.PLANNERS,'demo',LoopPlanner)
    monkeypatch.setattr(settings,'max_steps',2)
    owner=client.get('/api/auth/me').json()['id'];task_id=store.uid('test')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,owner,'test','生成报告','demo','pending','{}','','',store.now(),store.now()))
    asyncio.run(run_task(task_id,build_registry()))
    task=client.get('/api/tasks/'+task_id).json()
    assert task['status']=='failed'
    assert '最大' in task['error']
