"""Opt-in live LangChain acceptance using synthetic data, no credential access."""
import json
import time
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/LangChain轻量版验收'
OUT.mkdir(parents=True,exist_ok=True)
c=httpx.Client(base_url='http://127.0.0.1:8018',timeout=110)

def request(method,path,**kwargs):
    r=c.request(method,path,**kwargs);r.raise_for_status();return r

def task(body,label):
    t=request('POST','/api/tasks',json=body).json()
    for _ in range(100):
        t=request('GET','/api/tasks/'+t['id']).json()
        if t['status'] not in ('pending','running'):break
        time.sleep(1)
    (OUT/(label+'.json')).write_text(json.dumps(t,ensure_ascii=False,indent=2))
    assert t['status']=='succeeded',t.get('error') or t.get('result')
    print(label,'passed',flush=True)
    return t

request('POST','/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
settings=request('GET','/api/settings').json()
assert settings['framework']=='LangChain' and settings['model_adapter']=='ChatDeepSeek'
first=task({'task_type':'chat','mode':'live','prompt':'这次聊天的测试代号是星桥731，请记住，并用一句话确认。'},'第一轮真实对话')
second=task({'task_type':'chat','mode':'live','session_id':first['session_id'],'prompt':'我刚才告诉你的完整测试代号是什么？只回答代号。'},'第二轮上下文验证')
assert '星桥731' in second['result']
text='# 新增电力课堂约定\n\n本次试验中，青岚线路的演示复核编号是 DL-9472。编号仅用于本次课程验收。\n\n'+('负功率表示与参考方向相反，负载比值应取有功功率绝对值除以给定有功限值。\n'*28)
doc=request('POST','/api/assets',json={'name':'新增电力课堂约定.md','kind':'knowledge','content':text}).json()
assert doc['metadata']['splitter']=='RecursiveCharacterTextSplitter' and doc['metadata']['chunk_count']>1
qa=request('POST','/api/knowledge/ask',json={'question':'青岚线路的演示复核编号是什么？','mode':'live'}).json()
assert 'DL-9472' in qa['answer'] and any(h['document_id']==doc['id'] for h in qa['citations'])
(OUT/'新文档RAG问答.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print('新文档切分与真实 RAG passed',flush=True)
csv='line_id,active_power_mw,limit_mw\nQA1,100,100\nQA2,-120,100\nQA3,70,100\n'
a=request('POST','/api/assets',json={'name':'新线路现场输入.csv','kind':'dataset','content':csv}).json()
t=task({'task_type':'analysis','mode':'live','dataset_id':a['id'],'prompt':'分析全部线路，检索相关知识，生成辅助分析报告，列出超过给定有功限值的线路。'},'真实四工具分析')
stats=t['state']['statistics']
assert stats['total']==3 and stats['over_limit_count']==1
assert stats['items'][1]['loading_percent']==120
tools={e['payload']['tool_id'] for e in t['events'] if e['type']=='tool_completed'}
assert {'inspect_power_data','analyze_line_loading','search_knowledge','generate_power_report'}<=tools
report=request('GET','/api/assets/'+t['state']['report_id']).json()
(OUT/'线路分析报告.md').write_text(report['content'])
(OUT/'工具执行轨迹.jsonl').write_text(request('GET','/api/tasks/'+t['id']+'/trace').text)
summary={'status':'passed','framework':settings['framework'],'model_adapter':settings['model_adapter'],
    'splitter':settings['splitter'],'vector_store':settings['vector_store'],'live_multiturn':True,
    'new_document_rag':True,'line_count':3,'over_limit_count':1,'tools':sorted(tools),
    'tested_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
(OUT/'验收摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False),flush=True)
