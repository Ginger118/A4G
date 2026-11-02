"""Explicit opt-in real API acceptance test against the running local application.

Uses only synthetic course data and the built-in reviewer account. Does not read keys.
"""
import base64
import json
import sys
import time
from pathlib import Path
import httpx
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/真实模型验收'
OUT.mkdir(parents=True,exist_ok=True)
client=httpx.Client(base_url='http://127.0.0.1:8018',timeout=110)

def call(method,path,**kwargs):
    r=client.request(method,path,**kwargs)
    r.raise_for_status()
    return r

def log(message): print(message,flush=True)

def wait_task(task):
    previous=''
    for _ in range(180):
        task=call('GET','/api/tasks/'+task['id']).json()
        completed=[e['title'] for e in task['events'] if e['type']=='tool_completed']
        marker=f"{task['status']} / {','.join(completed)}"
        if marker!=previous: log(marker);previous=marker
        if task['status'] not in ('pending','running'):return task
        time.sleep(2)
    raise AssertionError('真实任务在验收时限内没有结束')

def save_task(task,label):
    (OUT/(label+'.json')).write_text(json.dumps(task,ensure_ascii=False,indent=2))
    trace=call('GET','/api/tasks/'+task['id']+'/trace').text
    (OUT/(label+'.jsonl')).write_text(trace)
    if task['status']!='succeeded': raise AssertionError(task.get('error') or task.get('result'))
    report=call('GET','/api/assets/'+task['state']['report_id']).json()
    (OUT/(label+'报告.md')).write_text(report['content'])

call('POST','/api/auth/login',json={'username':'reviewer','password':'Agent2026!'})
text='id,date,product,feedback\nN01,2026-11-02,设备 C,水箱漏水需要维修\nN02,2026-11-02,设备 C,快递延误尚未送达\nN03,2026-11-02,设备 D,连接设置很难理解\nN04,2026-11-02,设备 D,产品外壳开裂\nN05,2026-11-02,设备 C,退款申请后客服没有回复\n'
asset=call('POST','/api/assets',json={'name':'现场新反馈.csv','kind':'dataset','content':text}).json()
knowledge=call('POST','/api/assets',json={'name':'现场新增设备规范.md','kind':'knowledge','content':
    '# 现场新增设备规范\n\n课程模拟规范：设备 C 与设备 D 的质量反馈应在 6 个工作小时内首次响应。物流问题应在 1 个工作日内核查。\n\n特殊检测代码 ZX42 的检测周期是 17 个工作日。退款问题应核实订单进度后回复。使用问题提供对应操作指引。'}).json()
log('新 CSV 与新知识文档已导入')
qa=call('POST','/api/knowledge/ask',json={'question':'特殊检测代码 ZX42 的检测周期是多久？','mode':'live'}).json()
assert '17' in qa['answer'] and any(h['document_id']==knowledge['id'] for h in qa['citations']),qa
(OUT/'新知识问答.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
log('真实 RAG 问答通过：新知识命中，检测周期 17 个工作日')
task=call('POST','/api/tasks',json={'prompt':'分析已选客户反馈，统计所有问题类别、数量和占比，结合售后规范生成带引用的改进报告。','dataset_id':asset['id'],'mode':'live'}).json()
task=wait_task(task);save_task(task,'新输入完整任务')
assert task['state']['statistics']['total']==5
completed={e['payload']['tool_id'] for e in task['events'] if e['type']=='tool_completed'}
assert {'inspect_dataset','classify_feedback','aggregate_feedback','search_knowledge','generate_report'}<=completed
log('真实多步工具调用通过：5 条反馈计数正确')
follow=call('POST','/api/tasks',json={'prompt':'只看设备 C，重新生成分析报告。','dataset_id':asset['id'],'session_id':task['session_id'],'mode':'live'}).json()
follow=wait_task(follow);save_task(follow,'多轮产品筛选')
assert follow['state']['statistics']['total']==3
assert follow['state']['statistics']['products']=={'设备 C':3}
log('真实多轮跟进通过：设备 C 精确筛选 3 条')
image=Image.new('RGB',(1000,580),'white');draw=ImageDraw.Draw(image)
font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
title=ImageFont.truetype(font_path,34);font=ImageFont.truetype(font_path,26)
draw.rectangle((30,30,970,550),outline='#7760d5',width=4)
draw.text((65,70),'SERVICE TICKET # QA-2048',font=title,fill='#332244')
for y,line in enumerate(['Product: Water Purifier C','Problem: WATER LEAK','Observed: Water leaking from the tank seam','Requested action: Repair','Synthetic test fixture - no personal information']):
    draw.text((65,160+y*65),line,font=font,fill='#554466')
image_path=OUT/'视觉验收输入.png';image.save(image_path)
vision=call('POST','/api/vision',json={'image_base64':base64.b64encode(image_path.read_bytes()).decode(),'prompt':'读取图中的工单号、产品、问题及请求的处理方式，用中文回答。'}).json()
assert '2048' in vision['answer'] and ('漏水' in vision['answer'] or '泄漏' in vision['answer']),vision
(OUT/'真实图片理解.json').write_text(json.dumps(vision,ensure_ascii=False,indent=2))
log('真实视觉推理通过：工单 QA-2048 与漏水问题被识别')
summary={'status':'passed','new_input_total':5,'follow_up_total':3,'tools':sorted(completed),
         'rag_new_document':True,'vision_ticket':'QA-2048','model':vision['model'],
         'task_ids':[task['id'],follow['id']],'tested_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')}
(OUT/'验收摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
log(json.dumps(summary,ensure_ascii=False))
