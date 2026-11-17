import asyncio,json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import llm,storage as store
from app.config import settings
from app.streaming import ChatInput,chat_events

@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'})
        yield c

def events(response):
    assert response.status_code==200,response.text
    return [(b.splitlines()[0][7:],json.loads(b.splitlines()[1][6:])) for b in response.text.strip().split('\n\n')]

def test_delta_before_completion_and_generator_closed_on_stop(client,monkeypatch):
    monkeypatch.setattr(settings,'api_key','test-placeholder-only');closed=[]
    async def model(*a,**kw):
        try:
            yield '第一段'
            await asyncio.sleep(20)
            yield '不能到达的第二段'
        finally:closed.append(True)
    monkeypatch.setattr(llm,'stream_completion',model)
    owner=client.get('/api/auth/me').json()['id']
    async def run():
        stream=chat_events(ChatInput(question='流式测试',mode='live'),owner)
        first=await anext(stream);assert first['event']=='session'
        task_id=first['data']['task_id']
        assert (await anext(stream))['event']=='step'
        chunk=await asyncio.wait_for(anext(stream),1)
        assert chunk=={'event':'answer_delta','data':{'text':'第一段'}}
        assert store.one('SELECT status FROM tasks WHERE id=?',(task_id,))['status']=='running'
        await stream.aclose()
        t=store.one('SELECT * FROM tasks WHERE id=?',(task_id,));assert t['status']=='cancelled' and t['result']=='第一段'
        assert closed
    asyncio.run(run())

def test_stream_multiturn_and_owner_isolation(client,monkeypatch):
    monkeypatch.setattr(settings,'api_key','test-placeholder-only');seen=[]
    async def model(messages,**kw):
        seen.append(messages)
        for t in ['记住了，','代号是青枫。']:yield t
    monkeypatch.setattr(llm,'stream_completion',model)
    e=events(client.post('/api/chat/stream',json={'question':'请记住代号青枫','mode':'live'}))
    session=e[0][1]['session_id'];task=e[0][1]['task_id']
    assert ''.join(d['text'] for k,d in e if k=='answer_delta')=='记住了，代号是青枫。'
    assert e[-1][0]=='done'
    assert len(client.get('/api/conversations/'+session).json())==2
    events(client.post('/api/chat/stream',json={'question':'刚才是什么代号？','mode':'live','session_id':session}))
    assert any(m['content']=='请记住代号青枫' for m in seen[-1])
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert client.get('/api/conversations/'+session).json()==[]
    assert client.get('/api/tasks/'+task+'/events').status_code==404
    events(client.post('/api/chat/stream',json={'question':'正常问候','mode':'live','session_id':session}))
    assert not any(m['content']=='请记住代号青枫' for m in seen[-1])

def test_partial_error_never_success_done(client,monkeypatch):
    monkeypatch.setattr(settings,'api_key','test-placeholder-only')
    async def model(*a,**kw):
        yield '部分文字'
        raise llm.ModelUnavailable('教学故障')
    monkeypatch.setattr(llm,'stream_completion',model)
    e=events(client.post('/api/chat/stream',json={'question':'演示中断','mode':'live'}));id=e[0][1]['task_id']
    assert e[-1][0]=='error' and not any(k=='done' for k,d in e)
    t=client.get('/api/tasks/'+id).json();assert t['status']=='failed' and t['result']=='部分文字'
    assert len(client.get('/api/conversations/'+t['session_id']).json())==1

def test_upstream_custom_delta_precedes_node_completion(client,monkeypatch):
    monkeypatch.setattr(settings,'api_key','test-placeholder-only')
    async def classify(*a,**kw):return {'content':'{"intent_type":"document_qa","goal":"查询教学编号","requires_bos":false}'},{}
    async def model(*a,**kw):
        yield '教学编号是 '
        yield 'STREAM-47 [1]。'
    monkeypatch.setattr(llm,'completion',classify);monkeypatch.setattr(llm,'stream_completion',model)
    a=client.post('/api/assets',json={'name':'stream.md','kind':'knowledge','content':'教学编号 STREAM-47，用于流式引用测试。'}).json()
    e=events(client.post('/api/upstream/stream',json={'question':'教学编号是什么？','mode':'live','document_ids':[a['id']]}))
    first=next(i for i,(k,d) in enumerate(e) if k=='answer_delta')
    completed=next(i for i,(k,d) in enumerate(e) if k=='step' and d['stage']=='result_fusion')
    assert first<completed
    assert ''.join(d['text'] for k,d in e if k=='answer_delta')=='教学编号是 STREAM-47 [1]。'
    assert e[-1][0]=='done'

def test_analysis_replay_and_terminal_error(client):
    owner=client.get('/api/auth/me').json()['id'];id=store.uid('test')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(id,owner,'teaching','分析教学输入','demo','failed',store.dumps({'task_type':'analysis'}),'','教学失败',store.now(),store.now()))
    store.event(id,'answer_delta','教学部分正文',{'text':'部分报告'})
    e=events(client.get('/api/tasks/'+id+'/events'))
    assert e[0]==('answer_delta',{'text':'部分报告'}) and e[-1][0]=='error'
    assert not any(k=='done' for k,d in e)

def test_empty_stream_is_failure(client,monkeypatch):
    monkeypatch.setattr(settings,'api_key','test-placeholder-only')
    async def empty(*a,**kw):
        if False:yield ''
    monkeypatch.setattr(llm,'stream_completion',empty)
    e=events(client.post('/api/chat/stream',json={'question':'空输出测试','mode':'live'}))
    assert e[-1][0]=='error' and not any(k=='done' for k,d in e)
