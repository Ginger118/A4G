"""Two-page report authoring; requires reportlab and the recorded acceptance evidence."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'evidence/课程栈20261115'
out=ROOT/'docs/课程栈升级';summary=json.loads((base/'真实课程验收.json').read_text());persist=json.loads((base/'重启持久化.json').read_text());assert summary['status']==persist['status']=='passed'
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));F='STSong-Light';W,H=595,842;c=canvas.Canvas(str(out/'验证报告.pdf'),pagesize=(W,H));c.setTitle('序流 v0.5 课程存储与语义检索验证报告')
def text(x,y,s,size=11,color='#263a50'):
 c.setFont(F,size);c.setFillColor(HexColor(color));c.drawString(x,y,s)
def para(s,y,width=499,size=11):
 line=''
 for ch in s:
  if pdfmetrics.stringWidth(line+ch,F,size)>width:
   text(48,y,line,size);y-=18;line=ch
  else:line+=ch
 if line:text(48,y,line,size);y-=18
 return y

def frame(page,title):
 c.setFillColor(HexColor('#f7f9fc'));c.rect(0,0,W,H,fill=1,stroke=0)
 text(48,802,'序流 / A4G v0.5    本轮实测：2026-11-15',10,'#64778a');text(48,761,title,24)
 c.setStrokeColor(HexColor('#d3dce8'));c.line(48,738,547,738)
 text(48,30,'合成教学资料 · 本机联调 · 不代表生产系统或通用检索质量',9,'#64778a');text(520,30,str(page)+'/2',10)
frame(1,'课程组件已经实际参与问答')
y=para('目标：沿用三栏流式界面，把本地文件与字符向量基线，升级为课程中的对象存储、语义嵌入与向量数据库链路。',710)
# Four-step readable figure
labels=[('MinIO','保存 PDF 原件'),('EmbeddingGemma','本机 768维向量'),('Milvus','保存并检索片段'),('LangGraph / LLM','组织带来源回答')]
for i,(title,sub) in enumerate(labels):
 x=48+i*128;c.setFillColor(HexColor('#e8eef7'));c.roundRect(x,594,115,72,9,fill=1,stroke=0);text(x+8,639,title,10);text(x+8,614,sub,10)
 if i<3:text(x+117,625,'>',12)
text(48,560,'本轮真实验收',16)
checks=[('原件完整性','MinIO 读回与上传字节完全一致，SHA256一致。'),('语义检索','两页 PDF / 两条向量；换一种中文问法仍召回第1页。'),('回答与来源','周期：十七个工作日；编号：COURSE-7319，对应第2页。'),('重复与隔离','同一 PDF 重复上传返回相同资产；跨用户读取/选用均404。'),('重启持久化','重启 MinIO 与 Milvus 后，新进程检索和原件读回通过。'),('检索职责','重启后禁止 embed_documents，检索仍通过；未临时重嵌文档。')]
y=532
for title,body in checks:
 text(48,y,title,12);y=para(body,y-19,size=10.5)-7
text(48,258,'迁移与复现',16)
y=para('已有知识资料4份已迁移；加入本轮2份合成资料后再迁移6份。资产编号、页码与本地原件保留。课程服务使用独立数据卷与端口。',232)
y=para('工作目录：/Users/zz/Desktop/A4G；入口：http://127.0.0.1:8018/。操作手册提供启动、模型固定来源安装、迁移、测试输入和预期输出。源码架构提供类/函数与可搜索索引。',y-7)
text(48,110,'边界',13)
para('仅两份合成教学资料、两个中文问题；没有通用召回率评测。OCR、真实BOS、研究显式规划执行、生产并发与故障集群仍未验收。',88,size=10)
c.showPage();frame(2,'界面证据与检查结果')
c.drawImage(str(base/'中文语义问答与来源.png'),48,430,width=499,height=281,preserveAspectRatio=True,mask='auto')
text(48,409,'实际工作台：中文回答、右侧来源页码与受控原件入口。',10,'#64778a')
text(48,372,'本轮检查结果',16)
y=para('43项 Python 检查通过（2.55秒，5条PyMuPDF SWIG弃用警告）；3项前端流式协议检查通过。TypeScript/Vite构建通过，Vite更新至8.3.8后安装审计0漏洞。敏感信息检查及差异格式检查通过。',347)
y=para('真实 DeepSeek 回答：周期问题31个增量片段，完整请求1.869秒；编号问题16个片段，1.442秒。片段不是Token，两次不同问题不能作为通用性能排名。',y-8)
text(48,y-10,'证据与适用范围',16)
y=para('evidence/课程栈20261115/：真实课程验收.json、重启持久化.json、问答1/2.json、教学制度.pdf、自动测试.txt。上述数据均为本轮结果；历史v0.4成绩没有计作本轮成绩。',y-36)
y=para('本轮模型为公开 ggml-org EmbeddingGemma Q8_0 GGUF，文件哈希已与发布方核对，再导入本机 Ollama。课程配置默认使用此模型，文档及问题的嵌入不经过外部云服务；回答仍使用已授权DeepSeek。',y-8)
y=para('资料上传失败会撤回未发布资产；跨存储不是分布式事务，可能留下不可检索的孤立对象/向量。当前没有自动清理和生产级任务恢复保证。未执行Git提交或推送。',y-8)
c.save();print(out/'验证报告.pdf')
