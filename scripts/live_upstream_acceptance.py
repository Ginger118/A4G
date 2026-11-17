import base64,json,sys,time
from pathlib import Path
import httpx,pymupdf
OUT=Path(__file__).resolve().parents[1]/'evidence/上游升级20261113';OUT.mkdir(exist_ok=True)
c=httpx.Client(base_url=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8018',timeout=180)
def post(path,body):
 r=c.post(path,json=body);r.raise_for_status();return r
post('/api/auth/login',{'username':'reviewer','password':'Agent2026!'})
health=c.get('/api/health').json()
d=pymupdf.open()
for text in ['本资料仅用于合成教学验收，不是真实电力业务数据。','蓝槐线路的教学复核编号是 QH-5817。负载比值取功率绝对值除以给定有功限值。']:
 p=d.new_page();p.insert_text((60,100),text,fontname='china-s',fontsize=12)
raw=d.tobytes();d.close();(OUT/'教学验收输入.pdf').write_bytes(raw)
a=post('/api/documents/pdf',{'name':'教学验收输入.pdf','content_base64':base64.b64encode(raw).decode()}).json()
assert a['metadata']['pages']==2

def upstream(label,body):
 start=time.perf_counter();r=post('/api/upstream/stream',{'mode':'live',**body})
 events=[{'event':b.splitlines()[0][7:],'data':json.loads(b.splitlines()[1][6:])} for b in r.text.strip().split('\n\n')]
 (OUT/(label+'.json')).write_text(json.dumps(events,ensure_ascii=False,indent=2))
 assert events[-1]['event']=='done',events
 answer=''.join(e['data']['text'] for e in events if e['event']=='answer_delta')
 contract=next(e['data'] for e in events if e['event']=='plan')
 return events,answer,contract,round(time.perf_counter()-start,3)

q,answer,contract,qa_time=upstream('真实PDF问答',{'question':'资料中蓝槐线路的教学复核编号是什么？请给出引用。','document_ids':[a['id']]})
assert 'QH-5817' in answer,answer
assert any(e['data'].get('page')==2 for e in q if e['event']=='source')
assert contract['status']=='answered',contract
csv=post('/api/assets',{'name':'教学线路.csv','kind':'dataset','content':'line_id,active_power_mw,limit_mw\nQA1,100,100\nQA2,-120,100\nQA3,70,100\n'}).json()
md=post('/api/assets',{'name':'线路检查说明.md','kind':'knowledge','content':'线路 CSV 分析步骤：读取校验数据，计算给定有功限值的负载比值，检索定义并生成带来源报告。完成条件是检查与报告完成，发现越限也可以完成检查任务。'}).json()
before=len(c.get('/api/tasks').json())
e,answer,contract,plan_time=upstream('真实任务草案',{'question':'请为已选线路 CSV 制定给定有功限值检查与报告的分析步骤。','dataset_id':csv['id'],'document_ids':[md['id']]})
assert contract['status']=='ready_for_planner',contract
assert len(contract['plan_steps'])==4 and not contract['constraints']['execution_authorized']
assert len(c.get('/api/tasks').json())==before
summary={'tested_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'health':health,'data_source':'本轮新建两页合成教学 PDF、Markdown 和三行教学线路表','real_model_pdf_qa':'passed','page_provenance':2,'real_model_plan_draft':'passed','plan_steps':4,'no_execution':True,'qa_seconds':qa_time,'plan_seconds':plan_time,'unverified':['扫描页OCR','真实BOS','显式规划执行','MinIO/Milvus服务联调','预训练语义嵌入']}
(OUT/'验收摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
