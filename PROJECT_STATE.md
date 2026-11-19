# A4G最新补充：召回评估Demo · 2026-11-17

最近核对2026-11-17。用户希望先做几题自动标注/计分Demo占位、以后扩展。现v0.6基座新增知识库页“召回演示”，直达 http://127.0.0.1:8018/?view=knowledge#retrieval-demo 。本轮是系统模块补充，无新依赖或SQLite表；已空闲重启课程实例。本文替代历史“无召回评估入口”的当前口径，正式质量评估仍未完成。

- 固定8题`data/evaluation/recall_demo.json`（retrieval-demo.v1），按用户01—08文档主题预置参考，原件sha256在检索前冻结；label_status=demo_unreviewed。不是根据命中结果反推标签，也未经专家审核/穷尽相关性。
- `evaluation.py`提供认证GET `/api/evaluation/demo`、POST `/api/evaluation/demo/run`。沿用当前用户所有ready知识和原rag.search，不按参考答案限制范围；top4片段/原阈值，按参考文档版本去重计分。缺参考版本未评，均值仅含已评题且展示覆盖数；有参考但未命中记0，多参考可部分分。
- 结果按账号写`.runtime/retrieval-evaluations/`私密0600 JSON；每账号互斥，题集/语料哈希用于过期判断，期间变化拒绝发布。只有整轮完成才原子替换；服务失败明确提示且保留上次完整结果。记录后端/嵌入模型/阈值/时间，配置修改后应重跑；非分布式任务队列。
- `RetrievalDemo.tsx`在知识库页显示Demo标签、运行/均值/已评覆盖、每题参考与实际片段、相似度、问题带入和JSON导出；资料变更读回过期信息，顶部按钮和query/hash可直达。页面没有伪造固定百分比。
- 本次实测：当前11份知识、Milvus/Ollama EmbeddingGemma768维、阈值0.3，demo8题参考全部覆盖（含1题2份参考），平均文档级召回100%，1.643秒；独立按SQL原件版本重算一致，保存读回一致。reviewer缺参考版本，8题未评、均值null；无登录401，临时验收会话finally清理。仅检索，不调用DeepSeek回答模型。
- 100%是固定参考文档覆盖的演示结果，不是片段级召回、答案准确率、正式/独立留出质量。QA仍在语料里，命中潮流节点文档仍不代表召回到平衡节点表格行。正式扩展需另行审核标签、明确粒度、构建独立集，不能只去掉DEMO标签。
- 本轮最终64项后端/5个已知SWIG警告/3.09秒，原54+新增10；3项SSE检查及前端构建通过。新增去重/缺版本/隔离/过期/异常保留/互斥/期间变更/API认证检查是替身，不冒充真实服务。秘密扫描156文件及diff格式通过。本轮浏览器控制超时，仅HTTP/API及构建包核对，无点击/下载/手机/截图实测；原用户流程保留。未push。

交付`docs/召回演示/验证报告.pdf`1页图文实测报告已渲染目检、操作手册.md、系统架构图.html/.svg。原始结果`evidence/召回演示20261117/`已Git忽略，镜像`outputs/a4g_recall_demo/20261117/`保存最终源码/集成patch、题集、公开摘要、测试与报告构建源；`scripts/live_recall_demo_acceptance.py`可独立重现demo和reviewer验收（覆盖各自上次Demo结果）。沿原course启动命令运行。

下一步：用户用顶部“召回演示”体验；后续接人工审核/片段级标签/独立留出集与对照实验。本轮没有BOS、OCR或研究规划接入。维护记录2026-11-17：新增演示参考与自动计分，实测范围/局限以上述证据为准；不要把历史无评估入口或100%误解为当前正式质量结论。

---

# A4G最新补充知识库 · 2026-11-17

最近核对：2026-11-17。用户提供桌面PowerSystem-Agent-KB并授权加入。实际工作目录 `/Users/zz/Desktop/A4G`，业务版本仍v0.6.0、UI不变。入口 http://127.0.0.1:8018/；当前课程模式及真实DeepSeek可用，以本文最新补充为准。

- 已为demo体验工作空间导入01—09共9份MD、465块，实际各54/41/50/39/71/64/48/47/51块。00接入指南和JSON只读参考；文档推荐加载代码不执行，1200/150不覆盖现有420/60。YAML仍为原文，未新加元数据过滤。
- 来源 `/Users/zz/Desktop/PowerSystem-Agent-KB` 未改（文件哈希对照通过）；逐字节副本 `data/private/PowerSystem-Agent-KB/` 已Git忽略；MinIO保留原件。其他账号不自动共享，原资料与原任务不删除。
- 新增 `scripts/import_power_kb.py:plan/main`，默认预览，显式--apply才发布；调用原rag.add_document并逐块/原件核验，重复内容复用ID。新增 `scripts/verify_power_kb.py:main`，本机验收临时会话仅在内存生成，finally删除；无新增生产登录入口。
- 本次实测：9份原件读回一致、465块offset精确、9份重导入全部reused；认证资产列表列出9份、9个定向检索均返回片段。2条真实DeepSeek SSE完成且带正确归属来源：GOOSE/SV给出相关区别；PQ/PV/平衡节点问题只回答前两类并明确缺依据，平衡节点表格行未召回。这是链路检查通过、回答完整性有缺口，不是2/2专业准确率。
- 文件宣称60题，实际42个唯一Q标题；缺25—27、35—36、48—60。未改原文、未补写。QA已入检索，不能以同题充当独立留出评测，所有专业内容仍需审核。
- 失败与恢复：首次尝试新进程遇端口占用；首次在线验收确认已有服务是无模型/内存/本地配置。核对无进行中任务后，只关闭已核对的A4G空闲进程并用原course+授权DeepSeek参数启动，在线配置和服务检查通过。浏览器控制3次超时并结束，本轮仅HTTP入口200和认证API验证，无新界面实拍或交互成绩。不重用历史54项通过作为本轮测试。
- 秘密扫描首次发现公开config/.env.example含非占位凭据；保留Git忽略的0600本机私密备份后，仅清空示例凭据，运行配置未动且未输出原值。最终146文件secret guard与diff格式通过；没有提交/推送。保留本机.env/.course.env，不向新供应商传凭据。

交付：`docs/知识库补充/验证报告.pdf`一页已渲染目检；同目录操作手册、可搜索源码系统架构图.html/.svg。镜像 `outputs/a4g_kb/20261117/` 有脚本、报告构建源和公开摘要；原始执行记录 `evidence/知识库补充20261117/` 已忽略。启动沿用 `uv run --locked --extra enterprise python run.py --course --use-authorized-deepseek-env`；详细导入/预期/测试输入见手册。

下一步：用户刷新并用demo资料问答体验；表格切分/召回不完整作为后续单项优化样例，先补审核题集再做正式评估。BOS、OCR和研究规划范围未扩大。

维护记录：2026-11-17完成用户知识补充；证据、已知缺口和失败纠正见上述路径，本轮实测与历史成绩分开。后续接手先看此节，再看下方历史。

---

# PROJECT_STATE · 序流 / A4G v0.6 低前置条件优化

最近核对：2026-11-16。用户要求先做无需新增准备条件的优化并给缩限PDF。当前仅实施LCEL结构化意图、普通流式聊天窗口、新MD标题切分；不扩大为OCR/RAGAS/混合检索等完整路线图。名称与三栏UI保留。

## 当前入口与启动

工作目录 `/Users/zz/Desktop/A4G`，v0.6.0；http://127.0.0.1:8018/ 。课程启动 `uv sync --locked --extra enterprise`，`python3 scripts/course_stack.py up`，`uv run --locked --extra enterprise python run.py --course --use-authorized-deepseek-env`。沿用v0.5课程私密配置/数据卷/本地嵌入模型，未增加依赖、服务或模型。模型凭据只按已有授权用于DeepSeek，不输出、不写状态；sources只读未动。新电脑依旧需按v0.5手册准备原课程环境。

## 本轮关键实现与边界

- `upstream/intent_chain.py:classify_intent`：ChatPromptTemplate | RunnableLambda模型适配 | PydanticOutputParser(Intent)。仅解析错误最多补试一次；服务/网络异常直接报错，两次格式不合规明确error。无权限字段写入，无执行器接通。`graph.py:parse_intent`调用子链；原只读契约/程序校验仍生效。
- `memory.py:select_context`：普通流式聊天按owner/session读取最近200条候选，过滤无完整assistant回答的孤立user，LangChain trim_messages保留完整最近问答对。24000单位为UTF-8字节加消息开销的保守估算，不是精确模型Token；系统提示/当前问题保留，当前问题自身过目标也不截断。SQLite全历史不删除。`streaming.py:chat_events`单一写入，context_selected记录选中数量。旧非流式API和资料模式仍沿用原上下文策略；无摘要/跨会话记忆/Redis。
- `markdown_chunks.py:split_markdown`：代码围栏外ATX标题边界，LangChain MarkdownHeaderTextSplitter提供标题metadata，原文分节再420/60递归切分，offset逐块精确校验。`rag.add_document`仅新MD采用新版本，headers随来源返回。TXT/PDF保持原路径；Setext未支持。旧资料及同内容去重资产不自动重切，避免破坏已有索引与来源。
- `/api/settings`保留splitter原值，新增markdown_splitter和chat_context_budget；项目版本更新，不用说明文字破坏旧API契约。React构建布局未重做。

## 本轮验证与纠正

- 桌面最终 **54 passed / 5已知SWIG弃用警告 / 2.35秒**，原43+新增11；3项前端协议检查及构建通过。格式补试/拒绝、预算裁剪、孤立消息、用户会话隔离、MD重复标题/CRLF/代码围栏/精确offset为明确替身/本地检查，不称云故障实测。
- 真实链路：预置8对合成历史后1次真实模型追问，选中16条、答出初始测试代号；不是16条真实交互。1份新MD生成3块，offset/标题元数据通过；真实LCEL分类、本机Ollama/Milvus/MinIO及DeepSeek回答十九个工作日，来源属于所选文档。没有通用质量或性能收益结论。
- 初次桌面最终回归发现settings.splitter说明文字改变破坏原精确字段测试；改为原字段+新独立说明字段后54项通过。保存最终自动日志，失败原因在本记录保留。
- 真实验收脚本最初内嵌原教学密码的复制被自动审核拒绝；已改为从临时环境变量读取后获准执行，密码不持久化进新脚本。没有扩大数据/模型授权。
- Flash局部测试设计：核对haiku映射deepseek-v4-flash；仅发最小脱敏三项设计，60秒超时，终止进程组，无输出采纳。记录镜像Flash测试审查.txt；主控自验。

## 交付与下一步

`docs/精简优化/项目技术栈更新_缩限版.pdf`是2页更新与验证报告，已逐页渲染核查；同目录操作手册、系统架构图.html/.svg/.md、symbols.json。原五页全量选型建议保留，不与本轮完成范围混淆。原始事件和日志在已忽略 `evidence/精简优化20261116/`；镜像源码/备份/证据在 `outputs/a4g_priority/20261116/`。

下一步先体验本轮，再准备图文PDF和审核题集，分别推进OCR/评估；混合检索待单变量对照与迁移方案。研究规划/BOS/OCR/Redis/自动摘要均未实现，不推送GitHub。本轮仅本地更新。

维护记录：2026-11-16完成三项缩限迭代，证据、失败修正和范围见上；不把原路线图的后续项写成完成。下一步由用户确定准备后的OCR/评估范围。

---

## v0.5及此前历史

# PROJECT_STATE · 序流 / A4G v0.5 课程存储与语义检索

**最近核对：2026-11-15。以下为当前交接；旧版本原文保留为历史。**

## 当前用户目标与已实现

用户希望项目尽可能贴合已学课程，接受补齐 MinIO / Milvus / 语义Embedding。保留名称、三栏UI、流式对话和上游只读TaskContract；本轮没有扩大电力业务。核心链路已真实跑通：上传PDF/TXT/MD → MinIO原件 → LangChain切分 → 本地Ollama EmbeddingGemma Q8_0 / 768维 → Milvus → LangGraph检索/组织回答 → DeepSeek真实流式输出。SQLite仍保存会话、任务、来源与图检查点，CSV与报告应用存储未迁移。

## 工作目录与可操作入口

- `/Users/zz/Desktop/A4G`，v0.5.0。当前8018已从桌面目录以课程配置启动，`/api/health`实测ok/0.5.0。
- 启动：`uv sync --locked --extra enterprise`，`python3 scripts/course_stack.py init`，`python3 scripts/course_stack.py up`，`uv run --locked --extra enterprise python run.py --course --use-authorized-deepseek-env`。Docker Desktop和Ollama需运行；缺现有授权环境则按本机.env配模型凭据并省略最后授权参数。
- 入口：http://127.0.0.1:8018/ 。模型与工具页可查看Milvus/minio/768维语义模型；登录后 `/api/knowledge/status` 实际探测服务，不用配置显示冒充就绪。MinIO控制台19101；API19100；Milvus19538，健康端口19191。全部本机回环绑定，与课程原服务隔离。
- 课程配置 `.course.env` 由init生成随机本机存储凭据，0600且Git忽略；不要输出、复制进报告或提交。原模型配置与用户运行库保留；原授权仅向 https://api.deepseek.com 使用环境凭据。语义嵌入在本机完成。
- 新机器需按手册先准备DAY6同名镜像；本轮复用已安装的课程镜像，没有声称仓库包含容器镜像。模型固定来源安装：`uv run --locked --extra enterprise python scripts/install_course_embedding.py`；默认模型别名相同不表示不同来源/量化权重相同。

## 本轮源码及行为

- `embeddings.py`：OllamaSemanticEmbeddings，真实/api/embed；校验数量、维度、有限数值、归一化；模型摘要+维度+提示格式生成指纹。模型修改后重启应用并迁移，缓存不会热发现同名模型被替换。
- `rag.py`：publish_knowledge先pending，成功持久化索引才ready；失败撤回资产并尽力删除向量。add_document保存文本原件；search从SQLite取授权资料，按文档过滤，课程配置仅做问题嵌入和Milvus检索，不每次重嵌文档。旧模型/缺索引提示显式迁移，不静默回退字符向量。
- `repositories/milvus.py`：collection_name按用户和模型指纹隔离；index_documents固定chunk主键批量upsert；search_vectors强一致检索并与SQL授权chunk交集核对。
- `documents.py`：OriginalStore支持MinIO/本地，PDF逐页解析与页码/偏移/哈希保留；原件接口先校验归属。`course_status.py`与main.py增加认证后就绪探测；配置页显示实际选择的后端与嵌入模型。
- `scripts/migrate_course_knowledge.py`：逐资料迁移对象/向量，成功后更新元数据，保留ID与本地原件。`run.py --course`显式加载课程配置；不加参数保留旧字符/内存基线，但已迁移原件依然依赖MinIO读取。
- LangGraph、DeepSeek、SSE与研究规划边界沿用v0.4。Vite同主版本修复到8.3.8；React/TypeScript布局未重做。

## 本轮实测、历史与失败

- 桌面最终 **43 passed / 5 SWIG弃用警告 / 2.55秒**；前端3项协议检查通过，TypeScript/Vite构建通过，npm安装审计0漏洞，secret guard及diff格式检查通过。新增8项合同检查为明确替身，不能当真实服务成绩。
- 真实服务使用两份新合成教学资料（两页PDF及一份干扰MD）和两个中文问题。PDF对象字节/哈希读回相同、两页两向量、重复同文件返回同资产、资料范围过滤与跨用户404均通过。
- “多久检查一遍设备档案？”回答十七个工作日，首条来源第1页/0.6018；编号回答正确，首条第2页/0.5861。分别31/16个增量片段，完整请求1.869/1.442秒；片段不是Token，不是通用质量/性能排名。
- 实际重启A4G MinIO/Milvus容器后，新进程原件读回/检索通过；禁止embed_documents仍能检索，证明不是重嵌文档假装持久化。原知识4份迁移成功，加入本轮2份后重跑6份。
- 首次Ollama官方分发与Ollama的HF拉取因目标地址校验失败；公开HF文件直下载遇读超时，续传后333590944字节完整，SHA256与发布方相符，再本机导入成功。固定仓库修订、量化与哈希在 `docs/课程栈升级/模型来源.json`，不是把未下载模型写成已运行。
- Flash审查尝试：已核对本机haiku映射deepseek-v4-flash。仅传递一个最小的脱敏存储设计摘要（无密钥/原文），100秒超时，终止进程组，无输出被采纳。主控自行审查代码并完成回归与真实验收。记录位于镜像归档 `flash_review.txt`；实际服务模型响应未取得，不声称完成Flash评审。
- 浏览器核对v0.5配置页真实显示Milvus、minio、768维模型，并回放本轮中文回答和来源页码。历史v0.4流式/窄屏成绩不计入本轮新测试。

## 交付与证据

- `docs/课程栈升级/操作手册.md`：工作目录、前提镜像、启动、固定模型安装、测试输入/预期、迁移与重启。
- `docs/课程栈升级/验证报告.pdf`：两页图文，本轮结果及限制；已渲染人工核查。
- `docs/课程栈升级/系统架构图.html/.svg/.md`与symbols.json：本轮类、函数、路径、职责和调用逻辑，可搜索。
- 原始本地证据 `evidence/课程栈20261115/`（Git忽略）。镜像归档 `outputs/a4g_course_stack/20261115/`，含模型来源、公开源码备份、应用前备份、逐事件JSON、重启结果与截图。测试脚本：live_course_acceptance.py / verify_course_persistence.py。

## 边界与下一步

本轮只补课程核心存储/语义检索链路，未覆盖完整课程全部功能；OCR/混合检索/重排/生产并发/真实BOS/研究显式反馈规划仍未接入或验收。跨存储无分布式事务：失败可能留下不可检索的孤立对象/向量，本版不自动清理；服务异常不静默降级。应用不自动执行上游草案。全部为本地更新，未Git提交或push。下一步按用户课程检查项逐项核对，扩大真实检索题集后再讨论质量优化，保留研究规划接口。

## 维护记录

- **2026-11-15 · v0.5课程链路落地。** 用户授权贴近课程；MinIO/Milvus/本地768维语义嵌入已由真实端到端和重启验收支持，替代v0.4“仅有可选适配、未联调”结论。证据与限制见上及本轮报告。下一步先由用户按手册演示，再确定课程剩余项；未push。

---

## v0.4及更早交接存档

# PROJECT_STATE · 序流 / A4G v0.4 三栏流式聊天

**最近核对：2026-11-13。以下为最新交接；v0.3与更早记录保留在后方作为历史。**

## 最新要求与已完成行为

用户明确要求改变UI：像常见AI平台那样，上方是聊天记录、底部输入；左侧保留原导航，右侧集中放任务/来源/草案/材料，并像左侧一样可收起。此要求替代之前“保留全部原UI”的约束；名称仍保持“序流”及《基于 LangChain 的电力知识问答与辅助分析系统的设计与实现》。

本轮v0.4已实现三栏聊天工作台、左右独立折叠、窄屏详情抽屉、底部输入、Enter发送/Shift+Enter换行、真实文字流与停止、按回答查看右栏详情、切页保留会话、历史恢复和复制。普通聊天、资料回答、工具报告均按实际模型增量显示；固定程序草案与demo说明一次返回，不人为延时打字。

## 实际目录、启动与查收

- 继续编辑 `/Users/zz/Desktop/A4G`。本轮已从此目录启动8018，健康接口实测`ok / 0.4.0`；浏览器实际入口已登录教学账号并加载新版。8031只是隔离验收实例，已结束后不作为用户入口。
- 启动：`uv sync --locked`，`uv run --locked python run.py --use-authorized-deepseek-env`。仍仅向已授权的 `https://api.deepseek.com` 使用现有环境凭据；新环境自行在本机`.env`配置，不输出/提交凭据。前端首次安装或修改后在`src/frontend`执行`npm ci`、`npm run build`。
- 主入口：http://127.0.0.1:8018/ 。窄屏会收起侧栏；宽窗口显示三栏。右上“详情”打开/关闭右栏，顶部左侧按钮控制导航。
- 当前交付：`docs/流式聊天升级/操作手册.md`、两页`验证报告.pdf`、源码对应的`系统架构图.html/.md/.svg`与`symbols.json`。v0.3的`docs/上游升级/`和v0.2的`docs/项目图解/`为历史材料，不描述当前全部UI/流式行为。

## 关键实现与调用路径

1. `src/frontend/src/components/ChatWorkspace.tsx`：聊天记录、底部输入、工作模式、停止、滚动、历史选择和右侧四页签。`send()`根据模式使用对应SSE端点；`stop()`中断请求并取消执行任务。当前会话在切页时保持挂载，换账号清理选择状态。来源/草案属于被选择的回答，不与另一条回答串用。
2. `src/frontend/src/components/chat.css`：中性灰白三栏，主对话独立滚动，底部输入固定在对话列底部；左右收起释放空间。原style.css保留，新样式覆盖工作台和导航。`main.tsx`连接原导航、材料管理、历史和新工作台，并支持流中的代码围栏显示。
3. `src/frontend/src/sse.ts:readEventStream()`：POST/GET SSE、跨字节UTF-8与CRLF、error/done检查、断流检测和reader关闭。不是把完整文本用定时器切字。
4. `llm.py:stream_completion()`：真实`ChatDeepSeek.astream()`，只转发可见正文，关闭生成器时释放模型流，不发送隐藏推理。
5. `streaming.py:chat_events()`、`build_stream_router()`：`POST /api/chat/stream`即时传递普通聊天内容，读取当前owner/session历史；正常完成才存完整assistant消息。取消或断开标记cancelled，部分失败保留任务观察并发error，不发成功done。原非流式API保留兼容，但新聊天界面使用此流式端点。
6. `upstream/graph.py:compose_response()`与`service.py:upstream_events()`：LangGraph updates用于阶段，custom通过get_stream_writer转发模型正文，早于result_fusion节点完成；移除v0.3生成完再分64字传输的逻辑。只读契约及BOS未接通边界不变。
7. `tools/power.py:generate_power_report()`生成报告正文时保存answer_delta观察；`GET /api/tasks/{task_id}/events`每150ms取新观察发送。最后校验并保存正式报告，answer_final替换预览。非法引用或失败不能发布成功正式报告。
8. 原PDF页码、原件受控下载、字符哈希检索、用户隔离、Planner/Executor及课程工具保留。没有新增BOS、OCR、语义嵌入或任意业务写入。

## 本轮实测与证据

- 桌面最终目录Python检查 **35 passed / 5 warnings / 2.60s**（原29项+流式6项）；3项前端协议检查通过。SWIG弃用警告来自PyMuPDF，不是测试失败。测试使用独立临时数据库及明确替身，不把替身输出当模型实测。
- 本轮真实模型/网络接收验证：普通聊天558段，首段0.9106秒、结束5.3728秒；资料问答85段，首段1.6797秒、结束2.3291秒；工具报告215段，首段4.7631秒、结束7.2403秒。各一个不同教学任务，片段不是Token，不作通用性能或质量排名。
- 同会话追问保留12个要点上下文；真实长回答收4段后断开，服务端cancelled且无成功done；三行CSV仍为三条/一条越限、负功率120%。LangGraph增量在节点完成前到达；报告校验后正式替换。
- 浏览器实测：1280px下左244/中708/右328；关右栏中1036，双侧关中1280；390px下中间390、输入底部844，无横向溢出且详情抽屉可用。实际核对切页保留、历史资料回答恢复和右侧来源。最终正式8018入口也已打开。
- 原始本地证据：`evidence/流式聊天20261113/`；项目镜像归档：`outputs/a4g_chat_ui/20261113/evidence/`（逐事件时间、测试、截图及几何记录）。真实验收复现脚本为`scripts/live_chat_ui_acceptance.py`，前端协议检查为`src/frontend/tests/sse.test.cjs`。
- 失败与修正：首次界面核查发现旧.page-content宽度留下空白，已改为占满可用宽度；切页卸载导致会话视图丢失，已保持挂载；换账号清理新选择状态；停止/失败的部分文本不标成完整答案。证据边界与具体源码见手册、架构。

## 限制、Git与下一步

视觉入口仍是原独立HTTP响应，不声称视觉逐Token；未实现自动断线续传、任意节点恢复或生产并发保证。BOS、显式反馈规划、OCR、语义嵌入、Milvus/MinIO服务联调继续待验。上游草案仍不执行。

原`.env`、`.runtime`及用户材料保留；本轮部署前核对实际库无进行中任务，再重启8018。敏感信息检查和git diff --check通过。新增代码/文档均为本地改动，本轮未push；不要强行提交运行库、截图原始证据或私密配置。沿用现有secret guard与.gitignore。

下一步先让用户体验此版三栏和流式行为，再按明确反馈微调；后续数据/规划接口沿v0.3阶段计划推进，不为UI任务扩大电力业务。新迭代继续交付实测PDF、手册、源码架构并维护状态与资产地图。

## 维护记录

- **2026-11-13 · v0.4三栏与真实流式。** 用户新要求授权UI调整，替代v0.3保留全部原布局的限制。桌面35项及3项前端检查通过，三个新教学输入路径真实流式/停止/上下文验收通过，浏览器核查折叠、来源、历史和窄屏。交付本轮两页报告、手册、源码架构；原始证据位置和范围见上。下一步按用户体验反馈微调；未push。

---

## v0.3及更早交接存档（以下不代表当前UI或全部流式行为）

# PROJECT_STATE · A4G / 序流 v0.3

**最近核对：2026-11-13。当前权威状态以本节为准；下方v0.2记录仅作历史回查。**

## 最新用户要求与实际定位

用户要求依据《AI_Agent上游架构设计_课程衔接版.md》修改技术栈和产品定位，保留名称并继续优化；简单独立任务可用本机Claude Code的DeepSeek Flash/Pro。本轮保留正式题目《基于 LangChain 的电力知识问答与辅助分析系统的设计与实现》和“序流”名称、现有React布局与style.css，把产品扩展为“知识问答、材料理解与只读任务草案”。按设计文档分阶段实施，本轮不是整个目标架构全部落地。

## 当前工作与启动入口

- 实际目录：`/Users/zz/Desktop/A4G`；服务已从这里启动，核对 `http://127.0.0.1:8018/api/health` 返回 `ok / 0.3.0`。不要将隔离验收端口8029当作常驻入口。
- 启动：`cd /Users/zz/Desktop/A4G`，`uv sync --locked`，`uv run --locked python run.py --use-authorized-deepseek-env`。本机既有授权仅适用于 `https://api.deepseek.com`，不输出凭据；缺环境凭据时按本机`.env`配置后不加此选项启动。
- 当前可操作入口：http://127.0.0.1:8018/ 。工作台选择“任务理解与草案”；知识库可上传文字型PDF并查看页码和原件。
- 手册：`docs/上游升级/操作手册.md`；两页实测PDF：`docs/上游升级/验证报告.pdf`；源码对应架构及搜索索引：`docs/上游升级/系统架构图.html`（配套SVG/Markdown/symbols.json）。旧 `docs/项目图解/` 为v0.2历史图。

## 本轮已实现的技术栈和能力

- React + TypeScript / FastAPI + SSE / LangChain + LangGraph / PyMuPDF / SQLite应用表与图检查点 / uv.lock独立环境。前端只新增必要控件、记录与草案卡片；样式文件保持原样。
- `documents.py:ingest_pdf()`：10MB/100页以内文字型PDF，按页提取与切分、原文件内容哈希去重、页码/原文偏移/版本、归属校验后的原件查看；扫描空白页、加密与损坏PDF明确拒绝。原件默认落在`.runtime/originals`。
- `upstream/schemas.py`：`UpstreamRequest`、`Intent`、`PlanStep`、`TaskContract`；`upstream/graph.py:build_upstream_graph()`实际使用StateGraph和条件边，节点包括意图、对象、缺项、澄清、检索、回答/草案、程序校验。
- `upstream/validators.py:validate_contract()`检查能力白名单、输入引用、前提/依赖与未授权执行。当前四步草案来自已知能力目录，不是新数学规划算法。`ready_for_planner`仍为未执行、无执行授权，下游状态`not_connected`。
- `upstream/service.py:upstream_events()`产生阶段/来源/回答分段/澄清/草案/错误/终态事件。模型先完成回答再传输分段，不声称逐Token生成。错误不发送成功done。
- 每请求使用owner/session/request限定的SQLite图检查点，跨轮摘要和历史通过`storage.py`新建的`upstream_turns`表按owner/session隔离。刷新后可在执行记录页回看理解结果。重试重新校验本轮范围，不自动恢复任意中间节点；当前输入不会继承旧断面或数据集。
- `rag.py:search(...,document_ids=None)`先执行用户及文档范围约束，保留页码等来源；修正英文空格过早删除导致词面编号失配的问题。仍是透明的字符哈希基线，未接预训练语义嵌入。
- 可选适配：`repositories/milvus.py:search_vectors()`和`documents.py:OriginalStore`的MinIO分支；`uv sync --locked --extra enterprise`安装额外依赖。默认memory/local，不强制容器；本轮未服务联调，不把适配代码存在说成端到端服务验证。
- 新API：`POST /api/documents/pdf`、`GET /api/documents/{asset_id}/original`、`POST /api/upstream/stream`、`GET /api/upstream/sessions`。现有对话、RAG和四工具执行入口保持兼容。

## 本轮证据、模型分工与已知限制

- 桌面最终目录回归 **29 passed / 5 warnings / 7.43s**：旧20项 + 新9项（含参数化）。警告来自PyMuPDF SWIG类型弃用。使用独立临时库及明确模型替身；测试未清理或替换本地运行库。
- 新建两页合成教学PDF、Markdown、三行线路表，真实DeepSeek问答命中教学编号并引用第2页；四步草案有输入内容版本且未执行。单次总耗时3.123秒/0.961秒，只是当轮两条样例，不是通用时延或质量结论。
- 浏览器实际核查：登录、任务理解入口、阶段与来源、页码、未授权状态、历史回看。证据位于本机`evidence/上游升级20261113/`；项目镜像归档`outputs/a4g_upstream/20261113/evidence/`。源码集成工作区在镜像同目录`worktree/`，当前实际工作以桌面目录为准。
- Claude Code实际调用别名haiku，返回模型`deepseek-v4-flash`；只发送精简功能边界，输出10条候选验收建议；主控采纳来源、过度澄清、错误终态、BOS未接通及草案不授权检查原则，主控实现并实测，未调用Pro。原始输出和采纳说明在镜像`delegation/`，不作为系统已通过证据。
- 无效路径与纠正：全局Python搭配新SQLite Checkpointer发生`writes_sort_key`依赖错误，独立uv锁定环境修正；英文编号检索回归发现空格处理缺陷后修正。没有用回退伪造模型或服务成功。
- 尚未完成：扫描页OCR、预训练语义嵌入/混合检索/重排、MinIO/Milvus服务联调、真实BOS快照、MySQL/NL2SQL、显式反馈规划执行与任意中间节点自动恢复。当前草案不证明真实业务可执行；数值安全仍需下游独立验收。
- 本轮没有push，新增源码、图解、报告、锁文件和状态仍为本地改动。保留原.gitignore/提交前secret guard；不强制加入`.env`、`.runtime`、用户上传、证据或个人材料。公开报告仅含合成教学数据和摘要。

## 下一步

先按手册运行单机版本；后续单独验收真实嵌入与Milvus/MinIO的课程组件迁移，再取得脱敏BOS场景/同断面快照实现首个只读适配。不要一次注册全部RPC、引入任意SQL或将草案直接送真实执行。按用户要求决定是否提交/推送，不擅自变动私密配置或清库。

## 维护记录

- **2026-11-13 · 上游第一阶段整合。** 依据课程衔接设计升级为v0.3，交付可操作工作台、两页报告、复现手册和源码架构；桌面29项测试及两条新合成输入的真实模型链路通过。证据和范围见上文，v0.2安装/状态被本节替代是由于新图和检查点依赖要求独立环境；原始记录保留。下一步为真实嵌入和基础服务联调，之后才是BOS只读快照。

---

## v0.2交接存档（2026-11-09，以下不代表当前服务状态）

# PROJECT_STATE · A4G 课程 Agent 基座

**最近核对：2026-11-09。** 本文件用于其他对话接手桌面的 A4G 应用。先读本文，再核对最新用户要求、工作区差异和相关源码；完成有可复用成果的工作后，在当轮更新相关小节和文末维护记录。

## 1. 接手先看

- **实际工作目录：`/Users/zz/Desktop/A4G`。** 项目已从 ChatGPT 项目镜像内的 `enterprise-agent` 移到此处；旧目录不再是应用入口。不要在研究实验目录重建一套应用。
- **项目名称：**《基于 LangChain 的电力知识问答与辅助分析系统的设计与实现》，产品内名称“序流”，版本 `0.2.0`。
- **用户当前要求：**维护交接文件并提供路径，以便其他对话继续。本轮只做交接维护与离线测试，未改变业务、UI 或规划算法。
- **本轮实测：**已有自动测试 **20 passed，1 warning，10.58s**；核对时端口 `8018` 无监听，不能声称服务当前已运行。本轮没有真实模型调用、模型连通性验证或远端 Git 核验。
- **Git：**分支 `main`；本地 HEAD `ebdf0d0`，提交说明 `Initial release: LangChain power knowledge assistant`；远端配置为 `https://github.com/Ginger118/A4G.git`。历史已成功推送。当前本地 `origin/main` 指向同一提交；这不代表本轮联网检查过远端最新状态。
- **未提交成果：**`docs/项目图解/` 的十个文件，以及本次新增的 `PROJECT_STATE.md`。不要把它们误判为已在 GitHub 发布；保留现有文件，不清理或覆盖。

## 2. 已确认的目标与边界

这是一个可以独立交付、演示的常规 Agent 应用，同时为以后接入用户的显式指令规划方法保留基座。老师首先关心真实使用 LangChain、多轮对话、知识上传、RAG 切分和检索等基础能力。

电力是轻量业务背景：上传线路表，程序计算给定有功功率与限值的比值，结合知识检索生成辅助报告。用户明确要求控制复杂度，保留当前 UI 布局和样式；后续修改按明确需求进行，不擅自改版或引入复杂电网仿真。

当前规划器仍是常规 LLM Tool Calling。用户研究的显式规划、目标集合、动作前提/效果、失效传播及研究验收尚未接入。接口预留字段不等于这些机制已实现。早先的运行方式安全校核设计已被轻量定位替代，`docs/电力业务定位与研究对接方案.md` 是历史候选，当前范围以 `docs/轻量版定位与教师演示.md` 为准。

ChatGPT 项目中另有分层规划、七层数值实验与 BOS 静态调查。它们是独立研究原型，未集成进 A4G；不要把那些实验成绩写成这个应用的验收结果。当前也未完成毕业论文。

## 3. 已有功能与实现口径

| 能力 | 当前实现及限制 |
| --- | --- |
| 多轮对话 | 工作台默认入口，无需数据集；会话按用户隔离，最近六条历史交给模型；历史查询最多返回最近一百条。普通对话不会自动读取知识库或文件。 |
| 知识上传与切分 | 支持 TXT/Markdown，可预览实际片段、长度、原文起始位置和配置。`RecursiveCharacterTextSplitter`：上限 420 字符、目标重叠 60；短段之间不保证恰好重叠 60。 |
| RAG 问答 | LangChain `Document`、`Embeddings` 接口与 `InMemoryVectorStore`；答案附真实检索片段来源。原文/片段在 SQLite，向量索引在内存中按用户缓存、可重建。 |
| 嵌入基线 | 自定义 2048 维字符哈希与中文双字词面向量，余弦检索；不能介绍为预训练语义 Embedding。 |
| 工具分析 | 四工具为 `inspect_power_data`、`analyze_line_loading`、`search_knowledge`、`generate_power_report`；保留真实调用参数、结果、状态前后变化和报告。 |
| 数值定义 | CSV 三列 `line_id,active_power_mw,limit_mw`，最多 500 行；校验有限数值、正限值及线路标识。`abs(active_power_mw)/limit_mw*100`，严格大于 100% 才越限，恰好 100% 不计越限。不能据此推断整个电网安全。 |
| 模型接入 | 文本对话、问答、工具选择和报告正文通过 `langchain_deepseek.ChatDeepSeek` 的 `ainvoke` / `bind_tools`；实际可用性需在接手环境单独验证。 |
| 图片理解 | 保留独立模型 HTTP 适配，不能声称图片链路也由 LangChain 实现；不能将提取内容直接当作已核验的专业计算输入。 |
| 隔离与执行边界 | SQLite、scrypt 哈希密码、HttpOnly 会话 Cookie、按用户隔离资源；执行器校验权限/参数/超时/输出；默认最多 12 轮/次工具预算，同一工具连续失败三次停止。 |
| 历史兼容 | 旧版客户反馈工具、数据和证据保留以兼容历史任务；它们不是当前电力业务结果。 |

规则演示明确标记为 demo；真实模型失败不能伪装成成功或切换成未标记的模拟答案。LangSmith/旧版 LangChain tracing 在配置中关闭。

## 4. 源码与调用逻辑

以下路径均相对本工作目录，可在 VS Code 直接定位。

| 路径 / 符号 | 职责与衔接 |
| --- | --- |
| `run.py` | 检查已构建前端，将后端加入模块路径，启动本机 `127.0.0.1:8018`。 |
| `src/frontend/src/main.tsx`、`style.css` | React 交互界面与保留的 UI 样式；构建产物 `src/frontend/dist/` 不进 Git。 |
| `src/backend/app/main.py` | FastAPI 登录、文件、任务、会话、知识问答、图片和管理接口。`create_task()` 根据 `task_type` 分流对话或分析；`ask()` 为知识问答入口。 |
| `chat.py:run_chat_task()` | 组装历史与当前提问，调用模型并保存对话结果。 |
| `llm.py:completion()`、`langchain_completion()` | 文本调用经 ChatDeepSeek；兼容原规划协议并记录用量，模型错误显式失败；视觉走独立适配。 |
| `rag.py:add_document()`、`search()`、`LocalCharacterEmbeddings` | 上传切分并持久化片段；按用户构建/更新内存索引，返回来源、位置与分数。 |
| `agent/contracts.py:Planner` | `async decide(PlanningContext) -> PlannerDecision` 的可替换协议；决策为 `call_tool` / `finish` / `ask_user`。 |
| `agent/contracts.py:ToolSpec` | 工具参数模型、输出 schema、权限、版本及超时；`preconditions/effects/cost/uncertainty` 当前只是预留字段，执行器未实现研究语义。 |
| `agent/planners/llm_tool_calling.py:LLMToolCallingPlanner.decide()` | 真实模型选择工具并适配返回；按任务业务使用电力或历史反馈提示词。 |
| `agent/planners/demo.py:DemoPlanner` | 明确标记的规则演示策略。 |
| `agent/runtime.py:PLANNERS`、`run_task()` | 选规划器 → 取决策 → Executor → 更新状态/轨迹 → 下一轮；取消、预算、失败和最终报告核验在此处理。未来接规划器先从此入口适配。 |
| `agent/executor.py:Executor.execute()` | 权限、Pydantic 参数、异步超时、JSON Schema 输出校验与执行记录；与规划器分离。 |
| `tools/power.py:validate_power_csv()`、`build_power_registry()` | 轻量电力数据校验、工具注册、代码统计与报告生成。 |
| `storage.py`、`config.py` | 本地 SQLite 与产物；配置、运行目录、模型名称及 tracing 控制。 |

当前分析路径：`main.create_task()` → `runtime.run_task()` → `Planner.decide()` → `Executor.execute()` → 注册工具 → 写入实际结果与任务状态 → 再规划/完成/请求补充。知识工具复用 `rag.search()`；普通对话和直接知识问答有各自入口。

## 5. 如何打开、启动和复现

### 现有本机环境

在终端先进入实际工作目录：

```sh
cd /Users/zz/Desktop/A4G
/Users/zz/.pyenv/versions/3.12.6/bin/python3 run.py --use-authorized-deepseek-env
```

用户此前明确授权复用当前环境的现有模型凭据，**仅向 `https://api.deepseek.com` 发送**用于本项目调用。此启动选项从既有环境变量取值并在内存中传给固定地址，不持久化凭据。新对话不应打印环境、配置文件或密钥；若环境已无此变量，改按 README 在本机 `.env` 配置 `AGENT_API_KEY`。不要推断每个新会话都拥有同样的凭据。

启动后访问 `http://127.0.0.1:8018/`，健康接口 `http://127.0.0.1:8018/api/health` 应返回 `status=ok, version=0.2.0`。教学账号说明见 `README.md`，本交接文件不复制任何登录凭据。

现有本机 `dist/`、`node_modules/`、`.vendor/` 和 `.runtime/` 核对时存在，不必重复安装。换环境按 README 创建 Python 3.12 虚拟环境、安装 `requirements.txt`，并在 `src/frontend` 运行 `npm ci` 与 `npm run build`。推荐 Node.js 22。其他工作目录的默认 Python 可能不是现有 3.12 环境。

### 自动测试

```sh
cd /Users/zz/Desktop/A4G
PYTHONDONTWRITEBYTECODE=1 /Users/zz/.pyenv/versions/3.12.6/bin/python3 -m pytest -q -p no:cacheprovider tests
```

本轮预期且已观察到：`20 passed`。测试配置使用独立临时数据库；模型行为由明确的测试替身或 demo 验证，不是线上模型验收。只运行现有测试，不因本次文档维护额外引入业务测试。

### 给老师的五分钟演示

1. 多轮对话：告诉助手一个临时教学代号，再追问；应保留同一会话上下文。需真实模型配置。
2. 知识库：上传含独有教学信息的 Markdown，查看实际切分片段与偏移。
3. RAG：询问新文档独有内容，应有正确答案与实际来源引用。真实回答需模型配置。
4. 工具分析：上传三行 CSV，功率/限值依次为 `100/100`、`-120/100`、`70/100`。应得到三条线路、仅一条越限、第二条比值 120%，展示工具轨迹与报告。demo 报告会标记规则演示。
5. 模型与工具：展示真实 LangChain 组件及四工具定义。图片理解作为补充演示，单独确认模型能力。

真实验收脚本为 `tests/live_power_acceptance.py`，服务和真实模型配置就绪后运行，会产生模型费用并在本机 `evidence/LangChain轻量版验收/` 写入合成教学输入的结果。重跑前确认用户任务范围；不要拿历史文件冒充本轮结果。

## 6. 可交付图解与证据

- **可操作阅读入口：**`docs/项目图解/打开看图.html`，双击用浏览器打开；不依赖服务，包含两张内嵌 SVG 和讲解。
- **可编辑源图：**`docs/项目图解/A4G-思维导图与架构图.drawio`，两页；VS Code 安装 Henning Dieterichs 的 Draw.io Integration 后打开。PNG/SVG 可放进汇报。
- **Visio 版：**同目录的合并及单页 `.vsdx` 包含独立文本与图形，已做 ZIP/XML、关系目标和第三方页面/图形解析检查。**未在微软 Visio 中实机验证。** 当时尝试本机 LibreOffice 转 SVG 未能载入，自带公开模板也失败，因此没有完成该途径的可视化兼容性验证，不能把结构检查说成 Visio 实测。
- **讲解与打开方式：**`docs/项目图解/打开与讲解说明.md`；教师演示与业务边界见 `docs/轻量版定位与教师演示.md`。
- **历史真实验收：**`evidence/LangChain轻量版验收/验收摘要.json` 保存 `2026-11-02` 的通过记录，覆盖真实多轮、新文档 RAG、三条线路/一条越限和四工具闭环；本轮仅核对该文件存在与摘要。相关原始任务、报告和截图留在同目录，不提交 Git。
- **旧版本证据：**`evidence/真实模型验收/` 是历史客户反馈版，不替代当前电力验收。`evidence/自动测试记录.md` 等也是历史材料。

图解是静态文件，编辑 `.drawio` 不会自动同步现有 PNG/SVG、HTML 和 VSDX。更新时需要重新导出并统一内容；当时的生成脚本未作为项目稳定构建入口交付，不应依赖临时目录脚本长期存在。

按用户新确认的交付约定，**下一次系统迭代**需同时提供可操作可视化、通常 1–2 页且最多 5 页的图文验证报告 PDF、独立复现手册、对应源码类/函数的架构图，引用该轮实测并写明边界。当前 A4G 已有图解和 README/演示说明，尚未核对到符合该新约定的 A4G 验证报告 PDF；不能将另一个研究实验的 PDF 算作此处交付。本轮为状态文档维护，不宣称补齐系统迭代成果。

## 7. Git、私密信息与本地状态

- `.gitignore` 已排除真实环境文件、运行数据库、用户上传、证据、个人材料、密钥文件、缓存和本地依赖；仅保留公开空配置模板。不要强制添加这些目录。
- `scripts/check_secrets.py` 默认检查公开工作区；`--staged` 检查暂存内容，也拦截强制添加的私密路径。只输出路径和类别，不输出密钥值。
- 本机 `core.hooksPath=.githooks`，提交前执行检查；新克隆需执行 `git config core.hooksPath .githooks`。没有必要改变全局 Git 设置。
- `.runtime/` 包含本地用户与会话等状态，移动项目时已保留。不要为了演示或测试删除/重置它；测试应使用独立临时数据库。
- 先前实际 Git push 成功；GitHub 连接器失败、`gh` 未登录不代表原生 Git 不能认证。不要打印凭据排错。本轮没有发起 push。
- 交接文件仅保存摘要、方法和证据路径，不写 API Key、登录凭据、真实原始数据或生产对象标识。

## 8. 下一步与接手顺序

1. 先明确接手任务属于 A4G 应用还是独立规划研究，核对 `git status` 和本文件后继续；用户目前只要求交接，没有新功能待擅自开发。
2. 若要演示，先检查 8018 监听与健康接口，再按第 5 节启动；本轮没有启动常驻服务。先看阅读页也可以直接讲清整体。
3. 若用户要求继续交付，优先整理课程报告/答辩材料，并按新约定补齐 A4G 本轮实测 PDF、手册与源码对应架构；真实成员信息由用户提供，不编造。
4. 若用户要求接显式规划，从 `Planner` 协议、`runtime.PLANNERS`、工具语义与独立目标验收开始；复用执行器/工具/轨迹，避免先扩展复杂电力业务。接入尚需适配，不能直接把研究原型当成已接好的模块。
5. 图解与交接文件是否提交/推送，按用户后续要求和当前差异处理；先运行敏感信息检查，保留本地私密材料。

## 9. 维护记录

- **2026-11-02（历史）·** 完成 LangChain 轻量版与真实验收；依据 `README.md`、`evidence/LangChain轻量版验收/验收摘要.json`。完成桌面移位与初始推送，Git 提交 `ebdf0d0`；适用于课程 Agent 基座，不包含显式规划研究集成。
- **2026-11-03（历史）·** 新增思维导图、系统架构、可编辑 draw.io/Visio 与本地 HTML；依据 `docs/项目图解/` 十个文件及当轮工具记录。图片/阅读页检查完成，Visio 仅结构/页面解析核验；这些图尚未提交。
- **2026-11-09（本轮）·** 建立 A4G 专用交接文件并在 ChatGPT 项目根状态中增加分流入口。静态核对源码、图解、Git、历史验收摘要与本地依赖；重跑已有测试得 **20 passed / 1 warning / 10.58s**，警告为 Starlette TestClient 的 httpx 弃用提示。未调用真实模型、未联网核验远端、未修改应用代码。证据摘要见 ChatGPT 项目镜像 `outputs/A4G交接核对/20261109/核对记录.md`；下一步由用户在新对话指定，优先按第 8 节接手。


- **2026-11-15 · 课程技术栈更新建议（非系统迭代）。** 5页/23项对照见`docs/项目技术栈更新/项目技术栈更新.pdf`及同目录Markdown；基于用户清单、课程源码与近期聊天记录、官方文档静态调查。优先OCR/会话策略/结构化子链/评估，混合检索试验；其余按业务需求，不盲目换前端/向量库或引入NL2SQL。未改业务代码、未新增运行验收，待用户确定实施范围。源表与来源归档在项目镜像`outputs/项目技术栈更新/20261115/`。


## 紫色深浅主题补充 · 2026-11-16

用户要求深色模式保留紫色强调、左上Logo更明显，随后要求删除欢迎区中间单独的“序”。已在v0.6基础仅修改前端：theme.tsx的initial/useTheme/ThemeToggle安全读本地a4g-theme并设置html[data-theme]；theme.css覆盖语义配色及品牌渐变；main.tsx接入登录页与顶栏切换；ChatWorkspace.tsx删除welcome-mark，未删除左上品牌或聊天助手标识。默认dark，已有light选择保留，存储受限时只保证当前切换。

本轮TypeScript/Vite构建通过，浏览器实测深浅切换与刷新记忆、深色工作台/知识库/设置；修正右栏/详情/本地卡片残留白底，最终欢迎区无独立序字。未做模型调用/后端回归、手机专项或全部弹窗/对比度穷举；不把旧54项记为本轮新成绩。未升级业务版本、未Git提交/push。

交付docs/紫色深浅主题/验证报告.pdf（1页，已渲染核查）、操作手册.md、系统架构图.html/.svg。截图和前端源码/备份在镜像outputs/a4g_dark/20261116。下一步按用户视觉反馈调整，其他课程待办仍按v0.6范围。


## 头像弹窗收纳 · 2026-11-16

用户要求使用指南、紫色深浅拨动开关、当前模型/模式、模型与工具收进点击头像弹窗。已在v0.6前端完成：main.tsx App/openAccount/closeAccount维护状态与触发器焦点；AccountPanel.tsx渲染入口、Esc和外部点击；theme.tsx新增ThemeSwitch(role=switch/aria-checked)，account.css负责弹窗与侧栏滚动。顶栏原分散入口及左栏设置入口移除，退出也收进弹窗；侧栏折叠/窄屏有顶栏头像，忙任务仍禁止切换模式。

本轮构建通过；浏览器实测拨动深浅、真实/规则模式、指南/设置导航、Esc关闭并返回焦点、外部关闭、侧栏折叠入口。初次检查头像底部774px越过720px窗口；改最近列表滚动/底部不压缩后底部696px。没有调用模型/后端回归、手机专项、忙任务或退出登录实测；不声称这些通过。

交付docs/头像菜单/验证报告.pdf（1页已渲染）、操作手册.md、系统架构图.html/.svg。源码/备份/截图/证据在镜像outputs/a4g_account/20261116。无Git提交/push，研究/课程功能边界不变，下一步按交互反馈微调。


- **2026-11-17 · 后续人工补充的处理边界（静态核对）。** 页面知识库上传TXT/MD/文字PDF会自动提取、切分、保存原件、生成向量并发布索引，成功后可检索；处理仍在上传请求内等待，无持久化后台队列。直接向磁盘目录/对象存储放文件不触发监听；批量脚本只在显式运行时处理清单内文件。账号隔离、扫描OCR/旧版自动替换等边界保留。本次无系统修改或新运行验收；证据镜像outputs/a4g_kb/20261117/接入方式核对.md，对应main.py:upload/upload_pdf、rag.py:add_document/publish_knowledge和documents.py:ingest_pdf。后续人员优先使用页面上传。


- **2026-11-17 · 学习与讲解划分建议（静态）。** 建议按产品骨架、模型对话/记忆/流式、文档入库、RAG引用、Agent编排工具、工程验证六块学习；对应源码和演示路线在镜像outputs/a4g_learning/20261117/学习与讲解划分.md。仅教学建议，无功能修改或新验收；后续按用户选择逐块讲解，研究规划和BOS仍未实现。


- **2026-11-17 · 七页课设报告。** 用户要求六模块各一页加完整展示截图，已生成桌面/Users/zz/Desktop/课设报告.pdf：6页矢量技术/业务图及30处源码定位+1页11月16日真实完整界面截图；本轮浏览器2次超时，历史截图日期在PDF明确。全部7页渲染核查、页界与源码行号检查通过。构建源/源码索引/来源/核对记录在镜像outputs/a4g_course_report/20261117/。仅文档，无系统修改、新模型调用或全量回归；后续按报告模块讲解。


- **2026-11-17 · 课设报告源码融图细化版。** 用户要求移除独立代码定位表，将文件/函数/职责与调用安排放进图中。已替换桌面课设报告.pdf，仍7页：前6页36流程节点、60处代码定位（含重复）和串讲，末页沿用注明日期的11月16日真实完整截图。7页渲染目检、节点/页界与源码行号验证通过；Agent独立入口和工具反馈环明确。细化版构建/核对/预览/旧PDF备份在镜像outputs/a4g_course_report/20261117_细化版，前版档案保留。仅文档修改，无新系统实测；下一步按图讲解或依用户反馈继续细化。


- **2026-11-17 · 指标与存储入口核对。** 当前未实现Recall@k评估/看板，右侧来源与相似度不代表召回率。只读实查agent.sqlite3七表、upstream-checkpoints.sqlite3两内部表；MinIO19101、Milvus19191/webui与healthz均HTTP200，Milvus无凭据只读连接成功。MinIO登录对应.course.env的AGENT_MINIO_ACCESS_KEY/AGENT_MINIO_SECRET_KEY，实际值不写交接。证据镜像outputs/a4g_access/20261117/访问与指标核对.md。无系统修改/浏览器交互/新质量评测；召回率需独立标注集再实现评估。


- **2026-11-17 · 配置与重启手册。** 用户要求列出前后端、Docker和其他服务命令；已按实际源码与Docker/Ollama官方语义静态核对，交付docs/运行维护/启动与重启速查.md，镜像outputs/a4g_operations/20261117。8018是构建前端+API，5178仅前端开发；本机Ollama另需运行，SQLite无独立服务器，DeepSeek为云API。区分Docker restart与配置后up重建，说明.env/环境/授权参数优先级、嵌入模型更换需迁移、旧资料不自动重切。没有实际停止、启动或修改任何运行配置；后续按需要操作。


- **2026-11-17 · 数据库选型口径（静态建议）。** 用户询问SQLite产品化、课程PostgreSQL/MySQL及Navicat/Docker。核对本地课程DAY13-DAY15为MySQL+SQLAlchemy异步/Alembic；当前A4G仍SQLite7业务表+独立检查点，不因部署MySQL容器就自动迁移。建议图形看表可用支持SQLite的Navicat；课程对齐可另行迁移业务层到MySQL，检查点单独决定。证据镜像outputs/a4g_access/20261117/访问与指标核对.md；未启动新容器、未建立MySQL业务连接或迁移。

- **2026-11-18 · 课程讲解三件交付。** 续接11月17日中断任务，桌面课设报告更新为7页DayN对照版，另有桌面5页启动与配置重启手册。项目docs/课程讲解包含离线交互源码依赖图、静态SVG和课程证据对照。静态核对52维护文件、442定义、60报告源码定位、36节点映射及40条课程引用。构建、旧版报告备份及核对证据位于镜像outputs/a4g_three_deliverables/20261117。Flash审阅60秒超时无输出，课程映射据本机课程源码和复习记录完成。文档交付未启动、重启或迁移系统。

- **2026-11-18 · 源码依赖图与课程链接合并。** 项目 docs/课程讲解/源码依赖图.html 为统一入口，旧课程来源对照入口跳转。相关模块旁用橙色挂19个来自本轮附件的有道链接，映射据标题与源码，文章正文未能读取。后端目录按用户截图顺序，支持文件树、详情折叠、缩放平移、全屏及窗口内回退。Chrome离线验证交互及排列，原生全屏由浏览器宿主决定。镜像 outputs/a4g_source_graph/20261118 保存映射、构建、验证与旧版备份。此轮为讲解文档更新。
