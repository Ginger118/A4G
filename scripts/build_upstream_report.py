"""Rebuild the two-page report from THIS run's evidence; reportlab is authoring-only."""
from pathlib import Path
import argparse,json
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader

p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
summary=json.loads((a.evidence/'验收摘要.json').read_text());tests=(a.evidence/'自动测试.txt').read_text()
assert '29 passed' in tests and summary['real_model_pdf_qa']=='passed' and summary['real_model_plan_draft']=='passed'
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));font='STSong-Light';W,H=595.28,841.89
c=canvas.Canvas(str(a.output),pagesize=(W,H));c.setTitle('序流 v0.3 上游能力验证报告');c.setAuthor('A4G')
blue=colors.HexColor('#245cd6');ink=colors.HexColor('#183455');muted=colors.HexColor('#526680')
def text(x,y,s,size=10,color=ink):c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,s)
def para(y,s,size=10,leading=17):
 line=''
 for ch in s:
  if ch=='\n' or pdfmetrics.stringWidth(line+ch,font,size)>503:
   text(46,y,line,size);y-=leading;line='' if ch=='\n' else ch
  else:line+=ch
 if line:text(46,y,line,size);y-=leading
 return y

def head(page,title):
 c.setFillColor(colors.HexColor('#f5f8fd'));c.rect(0,0,W,H,fill=1,stroke=0)
 text(46,794,'A4G / 序流 · v0.3',11,blue);text(46,756,title,23)
 text(46,733,'2026-11-13  |  名称与布局保留，升级材料理解与只读任务草案',10,muted)
 text(46,30,'本轮新建合成教学数据；不代表真实 BOS 或生产业务验收。',8,muted)
 text(518,30,f'{page} / 2',8,muted)
head(1,'验证报告：从知识问答到任务草案')
for i,(value,label) in enumerate([('29 项通过','原20项 + 新9项'),('2 条真实链路','PDF问答 / 四步草案'),('0 次计划执行','草案与执行授权分离')]):
 x=46+i*171;c.setFillColor(colors.white);c.roundRect(x,637,160,72,9,fill=1,stroke=0);text(x+12,676,value,17,blue);text(x+12,653,label,10,muted)
y=603;text(46,y,'本轮实现与数据来源',15);y-=25
y=para(y,'使用两页新建教学 PDF、Markdown 和三行线路 CSV 验证。PDF 中的教学编号 QH-5817 可由真实 DeepSeek 回答，来源定位到第2页；线路表形成四步草案，输入绑定内容哈希，执行授权为 false。')
y=para(y,'核心栈：React / FastAPI + SSE / LangChain + LangGraph / PyMuPDF / SQLite / uv锁定环境。Milvus和MinIO已留可选适配，当前默认本地字符哈希检索与本地原文件。')
y-=10;text(46,y,'实际验收结果',15);y-=28
items=[('旧功能回归','20项通过：对话、隔离、旧工具、失败与边界。'),('新增自动测试','9项通过：PDF页码/偏移/去重/原件权限、扫描页拒绝、缺项澄清、草案不执行、范围检索、错误无成功done、能力与权限校验、历史隔离（含参数化）。'),('真实模型问答',f"回答命中教学编号并关联第2页；当轮单次总耗时 {summary['qa_seconds']} 秒。"),('真实模型草案',f"4步草案可交规划器检查，未执行工具；单次总耗时 {summary['plan_seconds']} 秒。不是普遍时延结论。"),('浏览器核查','原布局保留；阶段、回答、页码、原文入口可见；历史记录可回看。')]
for label,body in items:
 text(46,y,label,11,blue);y-=18;y=para(y,body,9.5,15);y-=9
text(46,100,'证据：本轮 evidence/验收摘要.json、自动测试.txt、真实模型事件与界面截图。',8.5,muted)
text(46,82,'限制：5条PyMuPDF SWIG弃用警告；模型、业务与数据隔离口径分别验收。',8.5,muted)
c.showPage();head(2,'调用逻辑、界面证据与下一步')
# Schematic with actual modules.
labels=[('React 工作台','任务理解与草案入口'),('FastAPI / SSE','routes.py / service.py'),('LangGraph 上游图','graph.py / schemas.py'),('来源与契约校验','rag.py / validators.py')]
for i,(t,b) in enumerate(labels):
 x=46+i*129;c.setFillColor(colors.HexColor('#eaf0ff'));c.roundRect(x,643,119,64,8,fill=1,stroke=0);text(x+7,681,t,10,blue);text(x+7,660,b,7.3)
 if i<3:text(x+121,672,'>',11,muted)
y=617;y=para(y,'PDF链路：upload_pdf -> ingest_pdf -> 按页提取/切分/版本 -> 私有原件存储。任务链路：意图、对象、缺项检查，进入澄清或检索/回答，最后校验 TaskContract。原 Executor 仅由工具分析路径使用。',9.5,16)
img=a.evidence/'任务草案界面.png'
if img.exists():
 reader=ImageReader(str(img));iw,ih=reader.getSize();scale=min(503/iw,270/ih);w,h=iw*scale,ih*scale
 c.drawImage(reader,46,y-16-h,width=w,height=h);y-=h+32
text(46,y,'尚未验证与明确边界',14);y-=24
y=para(y,'扫描页 OCR、预训练语义嵌入/混合检索、MinIO/Milvus服务联调、真实BOS快照、显式反馈规划执行尚未完成。检查点落库不代表能自动恢复任意中间节点。SSE为阶段事件和已生成文本分段，不宣称模型逐Token输出。',9.5,16)
y-=7;text(46,y,'复现与接手',14);y-=23
y=para(y,'在 /Users/zz/Desktop/A4G 执行 uv sync --locked，再按操作手册构建前端、配置本机凭据并启动。uv run --locked python -m pytest -q tests 复核自动测试。源码对应架构与可搜索符号索引见同目录系统架构图.html。',9.5,16)
y=para(y,'简单验收用例初筛使用本机 Claude Code / DeepSeek Flash，输出仅作候选；主控核对并运行上述测试。没有把模型建议或历史课程成绩当成本轮实测。',9.5,16)
c.save();print(a.output)
