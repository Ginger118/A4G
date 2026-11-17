# 当前版本v0.6：三项低前置条件优化

本轮仅完成LCEL结构化意图/一次格式补试、普通流式聊天完整问答与估算预算、新MD标题元数据及原文offset校验。无需新增依赖/服务/模型，现有课程配置与三栏UI沿用。

交付：`docs/精简优化/项目技术栈更新_缩限版.pdf`、操作手册、系统架构图.html。启动仍为`uv run --locked --extra enterprise python run.py --course --use-authorized-deepseek-env`。旧资料不自动重切，OCR/自动摘要/RAGAS/混合检索/研究规划未接入。下方旧版本文字按历史解释。

---

# 当前版本 v0.5：课程存储与语义检索

保留序流三栏流式界面和正式名称。课程配置采用 **MinIO + Ollama EmbeddingGemma + Milvus**，SQLite 保存应用记录与来源元数据；通过 `--course` 显式启用。下方 v0.4 与更早文字是历史说明，旧“尚未联调”结论以本轮验证报告为准。

```bash
uv sync --locked --extra enterprise
python3 scripts/course_stack.py init
python3 scripts/course_stack.py up
ollama pull embeddinggemma:300m
uv run --locked --extra enterprise python scripts/migrate_course_knowledge.py
uv run --locked --extra enterprise python run.py --course --use-authorized-deepseek-env
```

详细说明、课程对应表、验证边界与源码架构见 `docs/课程栈升级/操作手册.md`、`验证报告.pdf`、`系统架构图.html`。常规无课程配置启动仍保留字符向量/本地存储基线；不要将两种配置的实测结果混用。`.course.env` 包含随机生成的本机存储凭据，已忽略，不提交。

---

# 序流 电力知识问答与辅助分析系统

正式题目保持《基于 LangChain 的电力知识问答与辅助分析系统的设计与实现》。

## v0.4.0 当前版本 · 2026-11-13

工作台改为左导航、中间聊天记录和底部输入、可独立收起的右侧详情。任务、来源、草案和材料移到右栏。普通对话、资料回答与工具报告的模型正文使用真实增量输出，保留停止生成、多轮与历史回看；不把生成完的文本用定时器伪装为流式。

```sh
cd /Users/zz/Desktop/A4G
uv sync --locked
uv run --locked python run.py --use-authorized-deepseek-env
```

已有前端已构建；新环境按手册安装Node22并在src/frontend运行npm ci与npm run build。上述授权选项仅适用于当前本机既有DeepSeek凭据；新环境配置本机.env后不带该选项启动。打开 http://127.0.0.1:8018/ 。

[本轮操作手册](docs/流式聊天升级/操作手册.md) · [源码架构与索引](docs/流式聊天升级/系统架构图.html) · [两页验证报告](docs/流式聊天升级/验证报告.pdf) · [交接状态](PROJECT_STATE.md)。35项Python与3项前端协议检查通过；本轮真实模型验证了三个流式路径、停止和上下文。BOS/显式规划、OCR、语义嵌入及外部服务联调仍未完成。

## 以下为v0.3与v0.2历史说明

当前布局、流式行为与启动以顶部及本轮手册为准；以下保留历史能力与账号等说明。


题目保持：**基于 LangChain 的电力知识问答与辅助分析系统的设计与实现**。

## v0.3.0 当前版本（2026-11-13）

产品定位扩展为**电力知识、材料理解与只读任务草案**。原React布局保留，新增文字型PDF按页入库/来源/原件、LangGraph意图与澄清流程、SSE阶段事件、TaskContract草案校验及理解记录回看。草案不会自动执行，BOS与显式规划仍待接入。

当前核心栈：React + TypeScript、FastAPI/SSE、LangChain + LangGraph、PyMuPDF、SQLite检查点与应用存储、uv.lock独立集成环境。提供可选Milvus/MinIO适配，未做服务联调；默认仍为字符哈希检索与本地原文件，不能声称已有预训练语义检索或OCR。

```sh
cd /Users/zz/Desktop/A4G
uv sync --locked
# 首次安装前端或修改前端后：cd src/frontend && npm ci && npm run build && cd ../..
uv run --locked python run.py --use-authorized-deepseek-env
```

上述选项仅适用于本机已经授权且存在的环境凭据；新环境按空配置模板在本机 `.env` 设置 `AGENT_API_KEY` 后运行 `uv run --locked python run.py`。访问 http://127.0.0.1:8018/ 。完整安装、输入与预期结果见 [本轮操作手册](docs/上游升级/操作手册.md)，[源码架构与索引](docs/上游升级/系统架构图.html)，[两页验证报告](docs/上游升级/验证报告.pdf)，[接手状态](PROJECT_STATE.md)。

本轮29项测试通过；另用新建合成教学PDF与线路表完成真实模型问答和草案验收。部署环境和业务真实性分别验证，不把教学成功当真实BOS验收。上游输出结构并非完整规划算法。

## 以下为v0.2基础能力与历史说明

新版本安装启动以顶部和本轮手册为准；以下保留旧账号、原有功能与历史边界供回查。


当前题目：**基于 LangChain 的电力知识问答与辅助分析系统的设计与实现**。

v0.2.0 以课程基础能力为主：多轮对话、知识文档上传、真实切分与 RAG 引用问答、轻量工具分析及图片理解。电力是示例领域；本版不实现潮流、N−1、工况优化或复杂规划算法。页面布局与样式沿用 v0.1，调整业务文案并增加明确的对话/工具分析入口。

## 运行

推荐 Python 3.12、Node.js 22。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src/frontend
npm ci
npm run build
cd ../..
cp config/.env.example .env
# 在项目 .env 中填写 AGENT_API_KEY；空密钥只能运行明确标记的规则演示。
python run.py
```

访问 http://127.0.0.1:8018 。本地教学账号 `demo` / `Agent2026!`。管理员 `admin` 与隔离测试账号 `reviewer` 使用相同教学密码。密码以 scrypt 哈希保存，登录采用 HttpOnly Cookie，资源按用户隔离，服务只监听本机。

本次开发中用户已明确授权复用现有环境密钥向 DeepSeek 调用，可使用 `python run.py --use-authorized-deepseek-env`。该选项只把凭据提供给固定的 api.deepseek.com，不写入源码或磁盘。其他环境自行配置 `.env`。本地安装的 `.vendor` 仅用于开发环境，不进入工程包；正常安装通过 requirements.txt 完成。

## 给老师演示的顺序

1. **多轮对话**：工作台默认“多轮对话”，无需上传数据。先说一个测试代号，再追问刚才的代号，展示上下文。
2. **知识库上传与切分**：导入 TXT/Markdown。点文档打开预览，展开“切分片段预览”，可看到每段文字、长度、起始位置和切分配置。
3. **RAG**：询问新文档中的独有信息，展示答案与引用原文；换新文档后立即可检索。
4. **工具调用**：点击“体验示例任务”，选择线路数据，点击“线路数据分析”，执行并查看四个工具的真实记录与 Markdown 报告。
5. **LangChain 使用位置**：到“模型与工具”查看框架、模型适配、切分器、向量检索和工具契约。源码入口见下表。
6. **多模态**：图片理解继续调用真实视觉模型，不提供伪造识别。

## LangChain 真正用在何处

| 能力 | 组件 | 文件 |
| --- | --- | --- |
| 对话、问答、工具选择、报告正文 | langchain_deepseek.ChatDeepSeek，ainvoke / bind_tools | src/backend/app/llm.py |
| 知识切分 | RecursiveCharacterTextSplitter；420 字符上限、60 字符目标重叠，按段落和中文标点递归切分 | src/backend/app/rag.py |
| 文档与向量检索 | Document、Embeddings 接口、InMemoryVectorStore 余弦检索 | src/backend/app/rag.py |
| 多轮上下文 | 按用户与会话保存 messages，再交给 LangChain 模型 | src/backend/app/chat.py |
| 可替换规划器 | Planner / PlanningContext / PlannerDecision；保持执行器独立 | src/backend/app/agent/ |

嵌入采用自定义 2048 维字符哈希向量，是公开标记的本地词面基线，并非预训练语义模型。原始文本和片段持久化在 SQLite，内存向量索引会在重启或文档变化后重建。未启用外部 LangSmith 跟踪。视觉模型沿用独立适配，不能声称所有功能都由 LangChain 实现。

## 轻量电力业务

上传线路 CSV，三列为 `line_id,active_power_mw,limit_mw`。程序计算 `abs(active_power_mw) / limit_mw × 100%`，超过 100% 标记为超过给定有功限值。数值由代码计算，模型解释与报告建议需人工复核。

首批工具只有四个：读取线路数据、计算负载比值、检索电力知识、生成辅助报告。不据此判断整个电网安全，不执行真实调度。支持 500 行以内 CSV、2MB 内 TXT/Markdown 和 4MB 内图片。旧版客户反馈数据、测试和历史证据保留，相关兼容工具只在旧数据任务中使用，未伪装成新业务结果。

## 测试与证据

运行证据仅保存在本地，不提交到 GitHub；新环境可以执行下方真实验收重新生成。截图和执行轨迹可能包含用户输入，因此默认被 `.gitignore` 排除。

```sh
python -m pytest -q tests
# 服务已启动且已配置真实模型后，以下验收会产生少量模型调用费用：
python tests/live_power_acceptance.py
```

新增测试检查真实 LangChain 切分元数据和原文位置、用户隔离、数值有限性、负功率、边界值、工具闭环、多轮历史及框架配置。历史自动测试继续保留。真实验收使用新代号、新文档和新线路数据，结果输出到 `evidence/LangChain轻量版验收/`。

## 后续扩展位置

当前仍是常规 LLM 工具规划；`Planner.decide(context)` 接口与 Executor 分离。后续显式规划器可以复用同一套工具、权限、产物和轨迹，逐步补充目标判据与动作语义。不会为此提前建设复杂电网仿真或算法平台。早先的“运行方式安全校核”设计保留为历史候选，不作为当前开发范围。

教师演示与课题边界详见 `docs/轻量版定位与教师演示.md`。课设报告、答辩 PPT 和真实成员贡献材料仍待按最终实现整理，不包含在本轮软件改造的完成声明中。

## Git 与敏感配置

`.env`、本地运行数据库、用户上传文件、执行证据、个人材料、编辑器配置、密钥文件和本地依赖均不提交。仓库仅提供空的 `config/.env.example`。真实 API Key 请保存在本机环境或项目 `.env` 中。

本机已启用提交前检查。重新克隆后可运行 `git config core.hooksPath .githooks` 启用同样检查；也可手动运行 `python scripts/check_secrets.py --staged` 检查暂存内容。检查只报告路径与问题类别，不输出密钥值。不要用强制添加或跳过检查的方式上传本地私密文件。
