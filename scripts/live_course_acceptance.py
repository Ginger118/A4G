#!/usr/bin/env python3
"""Synthetic end-to-end acceptance against real local storage, embedding and model APIs."""
import argparse,base64,hashlib,json,time,sys
from pathlib import Path
import httpx,pymupdf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'.course.env',override=True)
from app.config import settings
from app.documents import OriginalStore
from app.repositories.milvus import _client,collection_name
p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8018');p.add_argument('--output',default='evidence/课程栈20261115');a=p.parse_args()
out=ROOT/a.output;out.mkdir(parents=True,exist_ok=True)
c=httpx.Client(base_url=a.url,timeout=180)
c.post('/api/auth/login',json={'username':'reviewer','password':'Agent2026!'}).raise_for_status()
status=c.get('/api/knowledge/status');status.raise_for_status();assert status.json()['ready'],status.text
# Entirely invented teaching rules; no operational power-grid instruction.
texts=['青岚演示站资料管理制度（合成教学样例）\n设备技术档案每隔十七个工作日核对一次。完成核对后，记录表应交给资料管理员留存。\n本样例仅讲述文档归档，不是设备操作规程。',
'青岚演示站来源追踪\n本份教学制度的核验编号为 COURSE-7319。技术档案核对周期适用于本样例，不代表真实电力企业规范。']
doc=pymupdf.open()
for text in texts:
 page=doc.new_page();page.insert_font(fontname='china-s');page.insert_textbox(pymupdf.Rect(60,60,530,750),text,fontname='china-s',fontsize=14)
raw=doc.tobytes();doc.close();(out/'教学制度.pdf').write_bytes(raw)
response=c.post('/api/documents/pdf',json={'name':'课程验收-青岚档案制度.pdf','content_base64':base64.b64encode(raw).decode()});response.raise_for_status();asset=response.json()
assert asset['metadata']['object_backend']=='minio' and asset['metadata']['vector_store']=='Milvus'
assert asset['metadata']['embedding_info']['semantic'] is True
readback=c.get('/api/documents/'+asset['id']+'/original');readback.raise_for_status();assert readback.content==raw
assert OriginalStore().get(asset['metadata']['original_key'])==raw
second=c.post('/api/documents/pdf',json={'name':'重复上传.pdf','content_base64':base64.b64encode(raw).decode()});second.raise_for_status();assert second.json()['id']==asset['id']
# A different document checks allowed-document filtering and distractors.
r=c.post('/api/assets',json={'name':'课程验收-会议安排.md','kind':'knowledge','content':'合成教学通知：会议室仅限每周五预约，午间停止使用。本通知不涉及设备技术档案核对周期。'});r.raise_for_status();other=r.json()
owner=c.get('/api/auth/me').json()['id'];info=asset['metadata']['embedding_info'];client=_client();name=collection_name(owner,info['fingerprint'])
try:
 rows=client.query(collection_name=name,filter='document_id == '+json.dumps(asset['id']),output_fields=['id','document_id','chunk_id'],consistency_level='Strong')
 assert len(rows)==asset['metadata']['chunk_count']
finally:client.close()
queries=[]
for question in ['这份资料规定，多久检查一遍设备档案？','教学文件的核验编号是什么？']:
 start=time.monotonic();r=c.post('/api/upstream/stream',json={'question':question,'document_ids':[asset['id']],'mode':'live','session_id':'course-acceptance'})
 r.raise_for_status();events=[]
 for block in r.text.strip().split('\n\n'):
  lines=block.splitlines();events.append({'event':lines[0][7:],'data':json.loads(lines[1][6:])})
 assert events[-1]['event']=='done',events[-1]
 hits=[e['data'] for e in events if e['event']=='source'];answer=''.join(e['data']['text'] for e in events if e['event']=='answer_delta')
 assert hits and all(h['document_id']==asset['id'] for h in hits)
 assert ('十七' in answer or '17' in answer) if len(queries)==0 else 'COURSE-7319' in answer
 queries.append({'question':question,'answer':answer,'sources':hits,'delta_count':sum(e['event']=='answer_delta' for e in events),'elapsed_seconds':round(time.monotonic()-start,3)})
 (out/f'问答{len(queries)}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
c.post('/api/auth/login',json={'username':'demo','password':'Agent2026!'}).raise_for_status()
assert c.get('/api/documents/'+asset['id']+'/original').status_code==404
assert c.post('/api/upstream/stream',json={'question':'查阅制度','document_ids':[asset['id']],'mode':'demo'}).status_code==404
summary={'date':'2026-11-15','scope':'本轮真实本地MinIO/Milvus/Ollama与DeepSeek；两份合成教学资料、两个问题，不代表通用检索质量','status':'passed','stack':status.json(),'object_roundtrip':True,'sha256':hashlib.sha256(raw).hexdigest(),'duplicate_same_asset':True,'vector_rows':len(rows),'chunks':asset['metadata']['chunk_count'],'owner_isolation':True,'document_filter':True,'queries':queries,'asset_id':asset['id']}
(out/'真实课程验收.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['queries','asset_id','stack','sha256']},ensure_ascii=False))
