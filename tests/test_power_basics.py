import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import storage as store,rag,llm
from app.agent.runtime import run_task
from app.chat import run_chat_task
from app.tools.power import validate_power_csv,build_power_registry

CSV='line_id,active_power_mw,limit_mw\nX1,100,100\nX2,-120,100\nX3,70,100\n'

@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'})
        yield c

@pytest.mark.parametrize('power,limit',[('NaN','100'),('10','0'),('10','-1'),('inf','100')])
def test_invalid_power_numbers(power,limit):
    with pytest.raises(ValueError):validate_power_csv(f'line_id,active_power_mw,limit_mw\nA,{power},{limit}\n')

def test_langchain_split_metadata_offsets_and_isolation(client):
    text='第一段是电力教学数据说明。'*30+'\n\n第二段说明负功率应取绝对值。'*30
    doc=client.post('/api/assets',json={'name':'切分测试.md','kind':'knowledge','content':text}).json()
    detail=client.get('/api/assets/'+doc['id']).json()
    meta=detail['metadata']
    assert meta['splitter']=='RecursiveCharacterTextSplitter'
    assert meta['vector_store']=='LangChain InMemoryVectorStore'
    assert meta['chunk_count']>1
    for c in meta['chunks']:
        assert len(c['text'])<=420
        assert text[c['offset']:c['offset']+len(c['text'])]==c['text']
    owner=client.get('/api/auth/me').json()['id']
    assert any(h['document_id']==doc['id'] for h in rag.search(owner,'负功率取绝对值'))
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    other=client.get('/api/auth/me').json()['id']
    assert all(h['document_id']!=doc['id'] for h in rag.search(other,'负功率取绝对值'))
    assert client.get('/api/assets/'+doc['id']).status_code==404

def test_power_end_to_end_boundary_and_negative_values(client):
    owner=client.get('/api/auth/me').json()['id']
    a=client.post('/api/assets',json={'name':'new-lines.csv','kind':'dataset','content':CSV}).json()
    assert a['metadata']['domain']=='power'
    task_id=store.uid('test')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,owner,'power-test','分析全部线路并生成报告','demo','pending',store.dumps({'input_id':a['id'],'business':'power','task_type':'analysis'}),'','',store.now(),store.now()))
    asyncio.run(run_task(task_id,build_power_registry()))
    task=client.get('/api/tasks/'+task_id).json()
    assert task['status']=='succeeded',task
    stats=task['state']['statistics']
    assert stats['total']==3 and stats['over_limit_count']==1
    assert stats['items'][0]['over_limit'] is False
    assert stats['items'][1]['loading_percent']==120
    report=client.get('/api/assets/'+task['state']['report_id']).json()
    assert '不执行潮流' in report['content']
    assert '120.00%' in report['content']
    tools=[e['payload']['tool_id'] for e in task['events'] if e['type']=='tool_completed']
    assert len(tools)==4

def test_multiturn_chat_receives_owned_history(client,monkeypatch):
    owner=client.get('/api/auth/me').json()['id']
    seen=[]
    async def model(messages,*args,**kwargs):
        seen.extend(messages)
        return {'content':'记住了，代号是青杉。'},{'total_tokens':12}
    monkeypatch.setattr(llm,'completion',model)
    session=store.uid('conversation')
    history=[{'role':'user','content':'请记住代号是青杉。'},{'role':'assistant','content':'记住了。'}]
    for m in history:
        store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),owner,session,m['role'],m['content'],store.now()))
    task_id=store.uid('chat')
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,owner,session,'我刚才说的代号是什么？','live','pending',store.dumps({'conversation':history,'task_type':'chat'}),'','',store.now(),store.now()))
    asyncio.run(run_chat_task(task_id))
    assert any(m.get('content')=='请记住代号是青杉。' for m in seen)
    assert seen[-1]['content']=='我刚才说的代号是什么？'
    assert client.get('/api/tasks/'+task_id).json()['status']=='succeeded'
    assert len(client.get('/api/conversations/'+session).json())==3
    client.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
    assert client.get('/api/conversations/'+session).json()==[]

def test_framework_is_visible_to_teacher(client):
    s=client.get('/api/settings').json()
    assert s['framework']=='LangChain'
    assert s['splitter']=='RecursiveCharacterTextSplitter'
    assert len(s['tools'])==4
