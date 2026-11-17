import httpx,json,time,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'evidence/流式聊天20261113';OUT.mkdir(exist_ok=True)
c=httpx.Client(base_url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8018',timeout=180)
def post(path,body):r=c.post(path,json=body);r.raise_for_status();return r.json()
post('/api/auth/login',{'username':'reviewer','password':'Agent2026!'})
def consume(label,path,body=None,stop_after=0):
 start=time.perf_counter();result=[];event='';data=[];deltas=0
 with c.stream('GET' if body is None else 'POST',path,json=body) as response:
  response.raise_for_status()
  for line in response.iter_lines():
   if line.startswith('event:'):event=line[6:].strip()
   elif line.startswith('data:'):data.append(line[5:].lstrip())
   elif not line and data:
    payload=json.loads('\n'.join(data));result.append({'event':event,'data':payload,'received_seconds':round(time.perf_counter()-start,4)});data=[]
    if event=='answer_delta':
     deltas+=1
     if stop_after and deltas>=stop_after:break
 (OUT/(label+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
 return result

def metrics(e):
 chunks=[x for x in e if x['event']=='answer_delta'];assert len(chunks)>2,e
 assert e[-1]['event']=='done',e
 assert chunks[0]['received_seconds']<e[-1]['received_seconds']
 return {'delta_count':len(chunks),'first_delta_seconds':chunks[0]['received_seconds'],'last_delta_seconds':chunks[-1]['received_seconds'],'done_seconds':e[-1]['received_seconds'],'characters':sum(len(x['data']['text']) for x in chunks)}
first=consume('真实聊天流','/api/chat/stream',{'question':'请用12个编号要点解释电力知识助手的用途，每点写两句话，覆盖对话、资料、引用、数据校验、工具、计划与人工复核。','mode':'live'})
chat=metrics(first);sid=first[0]['data']['session_id']
second=consume('同一会话追问','/api/chat/stream',{'question':'刚才要求列出几个要点？只回答数量。','mode':'live','session_id':sid})
answer=''.join(x['data']['text'] for x in second if x['event']=='answer_delta');assert '12' in answer or '十二' in answer,answer
stopped=consume('停止生成','/api/chat/stream',{'question':'请详细列出60个关于软件工程与电力知识学习的要点，每点至少30字。','mode':'live'},stop_after=4)
id=stopped[0]['data']['task_id']
for _ in range(40):
 t=c.get('/api/tasks/'+id).json()
 if t['status'] not in ('pending','running'):break
 time.sleep(.15)
assert t['status']=='cancelled',t['status']
assert not any(x['event']=='done' for x in stopped)
doc=post('/api/assets',{'name':'流式教学材料.md','kind':'knowledge','content':'流式教学助手的验收编号为 STREAM-984。它支持文档来源核对、会话理解和任务草案；只有真实返回才记为完成。'})
up=consume('资料问答流','/api/upstream/stream',{'question':'根据流式教学材料，先给出验收编号，再用五点说明它的用途，每点写两句并引用。','mode':'live','document_ids':[doc['id']]})
upstream=metrics(up)
assert 'STREAM-984' in ''.join(x['data']['text'] for x in up if x['event']=='answer_delta')
assert next(i for i,x in enumerate(up) if x['event']=='answer_delta')<next(i for i,x in enumerate(up) if x['event']=='step' and x['data']['stage']=='result_fusion')
post('/api/demo/seed',{})
a=post('/api/assets',{'name':'流式线路.csv','kind':'dataset','content':'line_id,active_power_mw,limit_mw\nQA1,100,100\nQA2,-120,100\nQA3,70,100\n'})
t=post('/api/tasks',{'prompt':'读取线路表，分析所有线路的给定有功限值负载比值，检索说明，生成简短报告。','dataset_id':a['id'],'task_type':'analysis','mode':'live'})
report=consume('工具报告流','/api/tasks/'+t['id']+'/events')
report_metrics=metrics(report)
final=c.get('/api/tasks/'+t['id']).json();stats=final['state']['statistics'];assert stats['total']==3 and stats['over_limit_count']==1
assert '120.00%' in next(x['data']['text'] for x in report if x['event']=='answer_final')
summary={'date':'2026-11-13','version':'0.4.0','data_source':'本轮新建合成教学问题、Markdown和三行CSV','chat_stream':chat,'context_followup':'passed','cancel_stops_without_done':True,'upstream_stream':upstream,'report_stream':report_metrics,'three_lines_one_over_limit':True,'note':'基于客户端实际接收时刻；不代表通用时延或质量成绩。'}
(OUT/'真实流式验收摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
