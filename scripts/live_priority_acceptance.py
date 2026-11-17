#!/usr/bin/env python3
"""Synthetic history + real model/MinIO/Milvus checks. Does not claim synthetic turns were real conversations."""
from pathlib import Path
import sys,json,time,os
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/backend'))
from app import storage as store
c=httpx.Client(base_url='http://127.0.0.1:8018',timeout=150)
c.post('/api/auth/login',json={'username':'reviewer','password':os.environ['A4G_ACCEPTANCE_PASSWORD']}).raise_for_status();owner=c.get('/api/auth/me').json()['id'];session=store.uid('priority')
out=ROOT/'evidence/精简优化20261116';out.mkdir(parents=True,exist_ok=True)
def events(response):
 response.raise_for_status();result=[]
 for b in response.text.strip().split('\n\n'):
  lines=b.splitlines();result.append({'event':lines[0][7:],'data':json.loads(lines[1][6:])})
 assert result[-1]['event']=='done',result[-1]
 return result
# Eight complete pairs are synthetic fixtures, not 16 real model turns.
for i in range(8):
 for role,content in [('user','记忆校验代号是晨雾-A6，请记住。' if i==0 else f'合成历史第{i}条普通确认。'),('assistant','合成确认，已记录。')]:
  store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),owner,session,role,content,store.now()))
e=events(c.post('/api/chat/stream',json={'question':'最开始的记忆校验代号是什么？只回答代号。','session_id':session,'mode':'live'}))
answer=''.join(x['data']['text'] for x in e if x['event']=='answer_delta');assert '晨雾-A6' in answer
id=e[0]['data']['task_id'];task=c.get('/api/tasks/'+id).json();assert task['state']['context']['selected_messages']==16
(out/'聊天事件.json').write_text(json.dumps(e,ensure_ascii=False,indent=2))
text='# 精简优化教学资料\n\n## 档案核对\n本份合成教学说明规定：档案每十九个工作日核对一次，原件交资料员留存。\n\n## 核验编号\n本轮教学编号为 PRIORITY-641。以上仅为软件测试资料，不是实际电力规范。'
r=c.post('/api/assets',json={'name':'精简优化-分章节说明.md','kind':'knowledge','content':text});r.raise_for_status();asset=r.json()
assert asset['metadata']['splitter_version']=='markdown-atx-offset-v1'
chunks=asset['metadata']['chunks'];assert len(chunks)==3
assert all(text[x['offset']:x['offset']+len(x['text'])]==x['text'] for x in chunks)
e=events(c.post('/api/upstream/stream',json={'question':'根据本文说明，档案多久核对一次？','document_ids':[asset['id']],'session_id':store.uid('priorityqa'),'mode':'live'}))
answer2=''.join(x['data']['text'] for x in e if x['event']=='answer_delta');assert '十九' in answer2 or '19' in answer2
sources=[x['data'] for x in e if x['event']=='source'];assert sources and all(x['document_id']==asset['id'] for x in sources)
assert any(x.get('headers',{}).get('h2')=='档案核对' for x in sources)
(out/'资料事件.json').write_text(json.dumps(e,ensure_ascii=False,indent=2))
result={'date':'2026-11-16','version':c.get('/api/health').json()['version'],'status':'passed','scope':'8对合成历史预置+1次真实追问；1份新MD+1次真实资料问答；真实本机MinIO/Milvus/Ollama及DeepSeek','synthetic_history_messages':16,'selected_history_messages':16,'memory_answer':answer,'markdown_chunks':len(chunks),'exact_offsets':True,'section_headers':True,'answer':answer2,'real_structured_chain':True,'context':task['state']['context'],'limits':'格式错误/预算裁剪为自动测试替身，不冒充真实模型故障；不是普遍性能质量评测'}
(out/'真实验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
