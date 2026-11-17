"""Two-page verification artifact. Requires reportlab in the authoring environment."""
from pathlib import Path
import argparse,json
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
s=json.loads((a.evidence/'真实流式验收摘要.json').read_text());u=json.loads((a.evidence/'界面核查.json').read_text());tests=(a.evidence/'自动测试.txt').read_text();assert '35 passed' in tests
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));F='STSong-Light';W,H=595.28,841.89
c=canvas.Canvas(str(a.output),pagesize=(W,H));c.setTitle('序流 v0.4 三栏流式聊天验证报告');c.setAuthor('A4G')
ink=colors.HexColor('#303b4c');muted=colors.HexColor('#7c899d');accent=colors.HexColor('#4e657f')
def text(x,y,v,size=10,color=ink):c.setFont(F,size);c.setFillColor(color);c.drawString(x,y,v)
def para(y,v,size=9.5,leading=16):
 line=''
 for ch in v:
  if ch=='\n' or pdfmetrics.stringWidth(line+ch,F,size)>503:
   text(46,y,line,size);y-=leading;line='' if ch=='\n' else ch
  else:line+=ch
 if line:text(46,y,line,size);y-=leading
 return y

def page(n,title):
 c.setFillColor(colors.HexColor('#f8fafc'));c.rect(0,0,W,H,fill=1,stroke=0)
 text(46,793,'A4G / 序流 v0.4  ·  2026-11-13',11,accent);text(46,754,title,23)
 text(46,729,'名称保留；左导航、中间聊天与底部输入、可收起的右侧详情。',10,muted)
 text(46,29,'数据为本轮新建合成教学输入；真实增量不等于完整业务或生产验证。',8,muted);text(520,29,f'{n} / 2',8,muted)
page(1,'验证报告：三栏聊天与真实流式输出')
for i,(n,label) in enumerate([('35 项通过','Python回归与流式行为'),('3 项通过','前端SSE协议边界'),('3 条真实流','聊天 / 资料 / 报告')]):
 x=46+i*171;c.setFillColor(colors.white);c.roundRect(x,638,160,70,9,fill=1,stroke=0);text(x+12,676,n,17,accent);text(x+12,654,label,9.5,muted)
y=605;text(46,y,'本轮改变了什么',14);y-=25
y=para(y,'ChatWorkspace独立管理聊天记录与底部输入。任务状态、来源、草案、材料移到右栏；左右都可收起。ChatDeepSeek.astream的可见正文直接经SSE传到浏览器；LangGraph用custom流发送正文，工具报告保存真实增量观察后发送。没有人为延时打字。')
y=para(y,'完整回复正常结束才写入assistant上下文。停止会关闭生成器，部分内容明确标为未完成。工具报告在正文生成时可预览，正式报告经数值和引用检查后替换预览。')
y-=12;text(46,y,'真实模型与客户端接收实测',14);y-=26
headers=[(46,'路径'),(170,'增量片段'),(275,'首段 / 秒'),(390,'结束 / 秒')]
for x,t in headers:text(x,y,t,10,accent)
y-=23
for label,key in [('普通聊天','chat_stream'),('资料问答','upstream_stream'),('工具报告','report_stream')]:
 m=s[key]
 for x,t in [(46,label),(170,str(m['delta_count'])),(275,f"{m['first_delta_seconds']:.3f}"),(390,f"{m['done_seconds']:.3f}")]:text(x,y,t,10)
 y-=24
c.setStrokeColor(colors.HexColor('#e1e7ef'));c.line(46,y+7,549,y+7);y-=14
y=para(y,'三条任务分别使用新合成问题、Markdown与三行CSV，输入不同，各测一次。片段数不是Token数；这些时刻证明正文在完成前到达，不支持通用速度排名。',9,15)
y-=9;text(46,y,'行为验收',14);y-=24
for label,body in [('停止与上下文','真实请求收到4段后主动断开，任务变为cancelled且无成功done；同会话追问记住12个要点。'),('计算与权限','三条线路中一条越限、负功率按绝对值计算；原回归与新增检查覆盖来源/用户隔离、部分失败、空流和取消关闭。'),('协议边界','前端逐字节UTF-8、CRLF拆帧、提前断流及错误终态均通过。Python测试使用明确替身，不冒充真实模型成绩。')]:
 text(46,y,label,10.5,accent);y-=18;y=para(y,body,9.2,15);y-=10
text(46,82,'证据：自动测试.txt、真实流式验收摘要.json、逐事件接收轨迹、界面核查.json。',8,muted)
text(46,65,'已知警告：5条PyMuPDF SWIG类型弃用；当前断言全部通过。',8,muted)
c.showPage();page(2,'界面证据、源码调用与复现')
img=ImageReader(str(a.evidence/'右栏引用来源.png'));iw,ih=img.getSize();scale=min(503/iw,285/ih);h=ih*scale;c.drawImage(img,46,710-h,width=iw*scale,height=h)
y=710-h-23
y=para(y,'浏览器核对：1280px桌面左244 / 中708 / 右328；关右栏中间1036px，双侧收起1280px。390px窄屏中间390px、输入底部844px，无横向溢出，详情可作抽屉展开。切页面后聊天保留；历史资料回答和右栏引用可恢复。',9.2,15)
y-=8;text(46,y,'对应源码与调用逻辑',14);y-=23
y=para(y,'main.tsx管理导航和历史选择 -> ChatWorkspace.tsx组织消息/输入/右栏 -> sse.ts读取与校验事件。普通聊天走streaming.py:chat_events -> llm.stream_completion -> ChatDeepSeek.astream；资料走LangGraph custom；工具报告走持久事件SSE，校验后answer_final替换预览。',9.2,15)
y-=8;text(46,y,'复现与当前限制',14);y-=23
y=para(y,'在 /Users/zz/Desktop/A4G 执行 uv sync --locked 后按操作手册启动，入口为127.0.0.1:8018。Python回归：uv run --locked python -m pytest -q tests；前端：在src/frontend执行npm run test:stream。真实验收脚本会调用模型并写本机evidence。',9.2,15)
y=para(y,'本轮专注聊天布局与文字流；OCR、语义嵌入、MinIO/Milvus服务联调、真实BOS与显式规划仍未新增。视觉入口保留原独立调用，不声称视觉逐Token流；未验证自动断线续传、任意节点恢复或生产并发保证。',9.2,15)
y=para(y,'可搜索的类/函数与行号、SVG架构及独立手册均在本报告同目录。原私密配置、运行数据与用户材料保留，本轮未自动推送。',9.2,15)
c.save();print(a.output)
