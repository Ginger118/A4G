import {useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {readEventStream} from '../sse';
import './chat.css';

type Mode='chat'|'upstream'|'analysis';
type Turn={id:string;role:'user'|'assistant';content:string;status?:'streaming'|'complete'|'error'|'stopped';sources?:any[];contract?:any;steps?:any[];error?:string;taskId?:string};
type Props={assets:any[];mode:'live'|'demo';model:string;resetKey:number;selection:any;seed:string;onBusy:(busy:boolean)=>void;onRefresh:()=>Promise<any>;onTask:(task:any)=>void;onUpload:(kind:'dataset'|'knowledge')=>void;onImage:()=>void;onSeed:()=>Promise<void>;renderMarkdown:(text:string)=>ReactNode};
const glyphs:Record<string,string>={panel:'M3 4h18v16H3zM15 4v16',left:'M3 4h18v16H3zM9 4v16',send:'M12 19V5m-6 6 6-6 6 6',stop:'M7 7h10v10H7z',plus:'M12 5v14M5 12h14',close:'m6 6 12 12M6 18 18 6',down:'M12 4v16m-5-5 5 5 5-5',file:'M5 3h9l5 5v13H5zM14 3v6h5',copy:'M9 9h11v11H9zM5 15H3V3h12v2',link:'m10 13 4-4M8 16l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m0 2 1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0',check:'m5 12 4 4L19 6',image:'M3 3h18v18H3z M3 17l6-6 5 5 3-3 4 4',clock:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 7v5l3 2'};
function G({name,size=18}:{name:string;size?:number}){return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={glyphs[name]||glyphs.file}/></svg>}
async function api(path:string,body?:unknown){const r=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'include',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});if(!r.ok){const e=await r.json();throw new Error(typeof e.detail==='string'?e.detail:'请求失败');}return r.json();}
const stageNames:Record<string,string>={intention_parse:'理解问题',entity_confirm:'确认材料',clarify_check:'检查条件',clarification:'整理补充问题',recall:'检索资料',result_fusion:'组织回答',validate_contract:'校验任务草案',model:'生成回答',tool_started:'正在调用工具',tool_completed:'工具已返回',planner_started:'选择下一步',planner_decision:'已确定下一步',task_completed:'任务已完成'};
const contractStatus:Record<string,string>={answered:'已回答',needs_clarification:'待补充条件',needs_evidence:'待补充依据',ready_for_planner:'草案待规划器检查'};
export default function ChatWorkspace(p:Props){
 const [turns,setTurns]=useState<Turn[]>([]),[question,setQuestion]=useState(''),[workMode,setWorkMode]=useState<Mode>('chat'),[busy,setBusy]=useState(false);
 const [session,setSession]=useState(''),[dataset,setDataset]=useState(''),[docs,setDocs]=useState<string[]>([]),[scene,setScene]=useState(''),[snapshot,setSnapshot]=useState('');
 const [open,setOpen]=useState(()=>{try{return localStorage.getItem('a4g-inspector')!=='closed'&&window.innerWidth>1100;}catch{return window.innerWidth>1100;}}),[tab,setTab]=useState<'task'|'sources'|'plan'|'materials'>('task'),[inspected,setInspected]=useState('');
 const [error,setError]=useState(''),[copied,setCopied]=useState(''),[atBottom,setAtBottom]=useState(true),[attach,setAttach]=useState(false);
 const scroll=useRef<HTMLDivElement>(null),input=useRef<HTMLTextAreaElement>(null),abort=useRef<AbortController|null>(null),liveTask=useRef(''),stick=useRef(true),busyRef=useRef(false),loadVersion=useRef(0);
 const datasets=p.assets.filter(a=>a.kind==='dataset'&&a.metadata.domain==='power'),knowledge=p.assets.filter(a=>a.kind==='knowledge');
 const latest=turns.filter(t=>t.role==='assistant').at(-1),detail=turns.find(t=>t.id===inspected)||latest;
 const update=(id:string,fn:(t:Turn)=>Turn)=>setTurns(v=>v.map(t=>t.id===id?fn(t):t));
 const panel=(value:boolean)=>{setOpen(value);try{localStorage.setItem('a4g-inspector',value?'open':'closed');}catch{}};
 useEffect(()=>{if(!dataset&&datasets.length)setDataset(datasets[0].id);},[p.assets]);
 useEffect(()=>{if(scroll.current&&stick.current)scroll.current.scrollTop=scroll.current.scrollHeight;},[turns]);
 useEffect(()=>{if(input.current){input.current.style.height='auto';input.current.style.height=Math.min(180,Math.max(48,input.current.scrollHeight))+'px';}},[question]);
 useEffect(()=>()=>{abort.current?.abort();},[]);
 useEffect(()=>{const media=window.matchMedia('(max-width:1000px)');const changed=()=>{if(media.matches)setOpen(false);};media.addEventListener('change',changed);return()=>media.removeEventListener('change',changed);},[]);
 useEffect(()=>{
  const version=++loadVersion.current;abort.current?.abort();setError('');setQuestion(p.seed||'');setTurns([]);setInspected('');setDocs([]);setScene('');setSnapshot('');stick.current=true;setAtBottom(true);
  const selected=p.selection;
  if(!selected){setSession('');setWorkMode(p.seed?'upstream':'chat');return;}
  const h=selected.upstreamRecord,selectedSession=h?.session_id||selected.session_id;
  setSession(selectedSession);setWorkMode(h?'upstream':selected.state?.task_type==='chat'?'chat':'analysis');
  if(!h)setDataset(selected.state?.input_id||'');
  Promise.all([api('/conversations/'+selectedSession),api('/upstream/sessions')]).then(async([messages,history])=>{
   if(loadVersion.current!==version)return;
   const items:any[]=messages.map((m:any,i:number)=>({...m,id:'history-'+i,order:m.created,status:'complete'}));
   for(const row of history.filter((x:any)=>x.session_id===selectedSession)){
    items.push({id:row.id+'u',role:'user',content:row.question,order:row.created+'a'});
    items.push({id:row.id,role:'assistant',content:row.response.answer,contract:row.response.contract,sources:row.response.sources,status:'complete',order:row.created+'b'});
   }
   if(!items.length&&h){items.push({id:h.id+'u',role:'user',content:h.question,order:h.created},{id:h.id,role:'assistant',content:h.response.answer,contract:h.response.contract,sources:h.response.sources,status:'complete',order:h.created+'b'});}
   if(!h&&selected.state?.task_type!=='chat'){
    let content=selected.result||selected.error||'任务仍在处理。';
    if(selected.state?.report_id){const report=await api('/assets/'+selected.state.report_id);content=report.content;}
    if(loadVersion.current!==version)return;
    setTurns([{id:selected.id+'u',role:'user',content:selected.prompt},{id:selected.id,role:'assistant',content,status:['failed','cancelled','interrupted'].includes(selected.status)?'error':'complete',error:selected.error,taskId:selected.id,steps:selected.events||[]}]);return;
   }
   if(!h&&['failed','cancelled','interrupted'].includes(selected.status))items.push({id:selected.id+'partial',role:'assistant',content:selected.result||'',status:selected.status==='failed'?'error':'stopped',error:selected.error||'本轮未完成',taskId:selected.id,order:selected.updated});
   setTurns(items.sort((a,b)=>a.order.localeCompare(b.order)));
  }).catch(e=>{if(loadVersion.current===version)setError(e.message);});
 },[p.resetKey]);
 async function send(){
  const q=question.trim();if(!q||busyRef.current)return;
  if(workMode==='analysis'&&!dataset){setError('请在右侧“材料”中选择线路 CSV。');setTab('materials');panel(true);return;}
  busyRef.current=true;setBusy(true);p.onBusy(true);setError('');setQuestion('');stick.current=true;setAtBottom(true);setAttach(false);
  const id=crypto.randomUUID(),controller=new AbortController();abort.current=controller;liveTask.current='';
  setTurns(v=>[...v,{id:id+'u',role:'user',content:q},{id,role:'assistant',content:'',status:'streaming',sources:[],steps:[]}]);setInspected(id);
  const receive=({event,data}:{event:string;data:any})=>{
   if(event==='session'){setSession(data.session_id);if(data.task_id)liveTask.current=data.task_id;}
   if(event==='answer_delta')update(id,t=>({...t,content:t.content+data.text}));
   if(event==='answer_final')update(id,t=>({...t,content:data.text}));
   if(event==='source')update(id,t=>({...t,sources:[...(t.sources||[]),data]}));
   if(event==='plan')update(id,t=>({...t,contract:data}));
   if(event==='step')update(id,t=>({...t,steps:[...(t.steps||[]),data],sources:data.stage==='tool_completed'&&Array.isArray(data.payload?.output?.hits)?data.payload.output.hits:t.sources}));
   if(event==='done')update(id,t=>({...t,status:'complete',taskId:data.task_id||liveTask.current||undefined}));
  };
  try{
   if(workMode==='analysis'){
    const task=await api('/tasks',{prompt:q,mode:p.mode,dataset_id:dataset,session_id:session,task_type:'analysis'});liveTask.current=task.id;setSession(task.session_id);p.onTask(task);
    await readEventStream('/tasks/'+task.id+'/events',undefined,controller.signal,receive);p.onTask(await api('/tasks/'+task.id));
   }else{
    const upstream=workMode==='upstream';
    await readEventStream(upstream?'/upstream/stream':'/chat/stream',{question:q,mode:p.mode,session_id:session,...(upstream?{dataset_id:dataset||null,document_ids:docs,scene_ref:scene||null,snapshot_ref:snapshot||null}:{})},controller.signal,receive);
   }
  }catch(e){const stopped=(e as Error).name==='AbortError';update(id,t=>({...t,status:stopped?'stopped':'error',error:stopped?'已停止生成，部分内容未作为完整答案保存。':(e as Error).message}));}
  finally{abort.current=null;liveTask.current='';busyRef.current=false;setBusy(false);p.onBusy(false);p.onRefresh().catch(()=>{});input.current?.focus();}
 }
 async function stop(){abort.current?.abort();if(liveTask.current){try{await api('/tasks/'+liveTask.current+'/cancel',{});}catch{/* Streaming chat cancellation is owned by the disconnected generator. */}}}
 async function copy(t:Turn){try{await navigator.clipboard.writeText(t.content);setCopied(t.id);setTimeout(()=>setCopied(''),1600);}catch{setError('复制失败，请直接选择文本复制');}}
 const show=(turn:Turn,target:'task'|'sources'|'plan')=>{setInspected(turn.id);setTab(target);panel(true);};
 return <div className={'chat-layout '+(open?'has-inspector':'')}>
  <section className="conversation" aria-label="对话工作区">
   <header className="conversation-header"><div><strong>序流</strong><span>{session?'当前对话':'新对话'}</span></div><button className={'quiet-button '+(open?'selected':'')} aria-label={open?'收起任务面板':'展开任务面板'} aria-expanded={open} onClick={()=>panel(!open)}><G name="panel"/><span>详情</span></button></header>
   <div className="chat-scroll" ref={scroll} onScroll={()=>{const s=scroll.current;if(s){stick.current=s.scrollHeight-s.scrollTop-s.clientHeight<100;setAtBottom(stick.current);}}}>
    {!turns.length?<div className="chat-welcome"><h1>有什么可以帮你？</h1><p>聊一个问题，读一份资料，或一起理清下一步。</p><div className="prompt-suggestions">{[['解释线路负载比值','chat','用通俗的话解释线路负载比值，并给一个简单例子。'],['根据资料回答','upstream','资料中蓝槐线路的教学复核编号是什么？请给出引用。'],['梳理分析步骤','upstream','为已选线路 CSV 制定给定有功限值检查与报告的分析步骤。']].map(([label,mode,q])=><button key={label} onClick={()=>{setWorkMode(mode as Mode);setQuestion(q);input.current?.focus();}}>{label}<G name="plus" size={14}/></button>)}</div></div>:<div className="chat-transcript" role="log" aria-label="聊天记录" aria-live="off">{turns.map(t=><article key={t.id} className={'chat-message '+t.role}>
     {t.role==='user'?<div className="user-bubble">{t.content}</div>:<><div className="assistant-label"><span>序</span>序流{t.status==='streaming'&&<small>正在生成</small>}</div><div className="chat-answer" aria-busy={t.status==='streaming'}>{t.content?p.renderMarkdown(t.content):t.status==='streaming'?<div className="thinking-indicator"><i/><i/><i/><span>{t.steps?.length?stageNames[t.steps.at(-1).stage]||'正在处理':'正在连接'}</span></div>:null}{t.status==='streaming'&&t.content&&<span className="stream-cursor"/>}</div>{t.error&&<div className={'message-note '+(t.status==='error'?'error':'')}><G name="clock" size={14}/>{t.error}</div>}<div className="message-actions">{t.content&&<button aria-label="复制回答" title="复制回答" onClick={()=>copy(t)}><G name={copied===t.id?'check':'copy'} size={15}/></button>}{!!t.sources?.length&&<button onClick={()=>show(t,'sources')}><G name="link" size={14}/>{t.sources.length} 个来源</button>}{t.contract&&<button onClick={()=>show(t,'plan')}>{contractStatus[t.contract.status]||'任务草案'}</button>}{(t.taskId||!!t.steps?.length)&&<button title="查看任务详情" aria-label="查看任务详情" onClick={()=>show(t,'task')}><G name="panel" size={15}/></button>}</div></>}
    </article>)}</div>}
   </div>
   {!atBottom&&<button className="jump-latest" aria-label="跳到最新消息" onClick={()=>{stick.current=true;setAtBottom(true);if(scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight;}}><G name="down"/></button>}
   <footer className="chat-input-dock"><div className="input-shell"><textarea ref={input} aria-label="发送消息" placeholder="给序流发送消息…" value={question} maxLength={6000} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();send();}}}/><div className="input-toolbar"><div className="input-tools"><div className="attachment-control"><button className="round-tool" aria-label="添加附件" aria-expanded={attach} onClick={()=>setAttach(!attach)} disabled={busy}><G name="plus" size={21}/></button>{attach&&<div className="attachment-menu"><button onClick={()=>{p.onUpload('knowledge');setAttach(false);}}>上传知识文档 / PDF</button><button onClick={()=>{p.onUpload('dataset');setAttach(false);}}>上传线路 CSV</button><button onClick={()=>{p.onImage();setAttach(false);}}>图片理解</button></div>}</div><select aria-label="工作模式" value={workMode} disabled={busy} onChange={e=>setWorkMode(e.target.value as Mode)}><option value="chat">多轮对话</option><option value="upstream">资料问答与草案</option><option value="analysis">工具分析</option></select><button className="material-shortcut" title="选择材料" onClick={()=>{setTab('materials');panel(true);}}><G name="file" size={15}/><span>{workMode==='chat'?'添加材料':dataset?'已选线路表':'选择材料'}</span></button></div>{busy?<button className="send-round" aria-label="停止生成" title="停止生成" onClick={stop}><G name="stop" size={18}/></button>:<button className="send-round" aria-label="发送消息" title="发送消息（Enter）" onClick={send} disabled={!question.trim()}><G name="send" size={19}/></button>}</div></div>{error&&<div className="composer-error" role="alert">{error}<button onClick={()=>setError('')} aria-label="关闭提示">×</button></div>}<p className="input-footnote">{p.mode==='demo'?'本地规则演示 · 未调用 AI 模型':'AI 可能会出错，请核对重要信息。'}<span>Shift + Enter 换行</span></p></footer>
  </section>
  {open&&<aside className="chat-inspector" aria-label="任务详情面板"><header><div><G name="panel"/><strong>对话详情</strong></div><button aria-label="关闭任务面板" className="quiet-button" onClick={()=>panel(false)}><G name="close"/></button></header><nav className="inspector-tabs" aria-label="详情分类">{([['task','任务'],['sources','来源'],['plan','草案'],['materials','材料']] as const).map(([key,label])=><button key={key} aria-selected={tab===key} onClick={()=>setTab(key)}>{label}{key==='sources'&&!!detail?.sources?.length&&<small>{detail.sources.length}</small>}</button>)}</nav><div className="inspector-scroll">
   {tab==='task'&&<><div className="inspector-section"><span className="inspector-eyebrow">当前状态</span><h3>{busy?'正在处理':detail?.status==='error'?'本轮未完成':detail?.status==='stopped'?'已停止':detail?'已返回':'准备就绪'}</h3><p>{detail?.contract?contractStatus[detail.contract.status]:workMode==='chat'?'连续对话，逐步生成回答。':'根据任务选择工具或整理草案。'}</p></div><div className="inspector-section"><h4>处理过程</h4>{detail?.steps?.length?detail.steps.filter((s:any)=>s.stage!=='answer_delta').map((s:any,i:number)=><div className="inspector-step" key={i}><span/><div><strong>{s.title||stageNames[s.stage]||s.stage}</strong>{s.payload?.tool_id&&<small>{s.payload.tool_id}</small>}</div></div>):<p className="inspector-empty">开始对话后，在这里查看实际处理过程。</p>}</div>{detail?.taskId&&<div className="inspector-section"><a className="inspector-link" href={'/api/tasks/'+detail.taskId+'/trace'} target="_blank" rel="noreferrer"><G name="file" size={15}/>下载执行轨迹</a></div>}</>}
   {tab==='sources'&&<div className="inspector-section"><span className="inspector-eyebrow">回答依据</span><h3>引用来源</h3>{detail?.sources?.length?detail.sources.map((h:any,i:number)=><details className="source-item" key={i}><summary><span>{i+1}</span><div><strong>{h.document}</strong><small>{h.page?`第 ${h.page} 页 · `:''}片段 {h.chunk_id}</small></div></summary><p>{h.text}</p>{h.page&&<a target="_blank" rel="noreferrer" href={'/api/documents/'+h.document_id+'/original#page='+h.page}>查看原 PDF ↗</a>}</details>):<p className="inspector-empty">普通对话不会自动检索资料。选择“资料问答与草案”后，实际引用会显示在这里。</p>}</div>}
   {tab==='plan'&&<div className="inspector-section"><span className="inspector-eyebrow">任务理解</span><h3>{detail?.contract?contractStatus[detail.contract.status]:'还没有任务草案'}</h3>{detail?.contract?<><p>{detail.contract.goal?.description}</p>{detail.contract.missing_fields?.length>0&&<div className="clarification-list"><h4>需要补充</h4>{detail.contract.missing_fields.map((m:string)=><p key={m}>• {m}</p>)}</div>}{detail.contract.plan_steps?.map((s:any,i:number)=><div className="plan-step" key={s.step_id}><span>{i+1}</span><div><strong>{s.purpose}</strong><small>{s.capability_id}</small></div></div>)}<div className="scope-note">此处为只读草案，未授予执行权限；下游规划器尚未接入。</div><details className="contract-json"><summary>查看结构化契约</summary><pre>{JSON.stringify(detail.contract,null,2)}</pre></details></>:<p className="inspector-empty">在输入框选择“资料问答与草案”，描述目标，即可确认条件和后续步骤。</p>}</div>}
   {tab==='materials'&&<><div className="inspector-section"><span className="inspector-eyebrow">本轮材料</span><h3>数据与知识</h3><label className="inspector-field">线路数据<select aria-label="选择任务数据" value={dataset} onChange={e=>setDataset(e.target.value)} disabled={busy}><option value="">未选择</option>{datasets.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label><div className="material-buttons"><button disabled={busy} onClick={()=>p.onUpload('dataset')}>上传 CSV</button><button disabled={busy} onClick={()=>p.onUpload('knowledge')}>上传文档 / PDF</button></div><h4>知识文档 <small>{knowledge.length}</small></h4>{knowledge.length?knowledge.map(a=><label className="document-choice" key={a.id}><input type="checkbox" checked={docs.includes(a.id)} disabled={busy} onChange={e=>setDocs(v=>e.target.checked?[...v,a.id]:v.filter(id=>id!==a.id))}/><span>{a.name}<small>{a.metadata.chunk_count} 个片段</small></span></label>):<p className="inspector-empty">还没有知识文档。</p>}<p className="field-help">未勾选时检索当前账号的全部知识文档。仅“资料问答与草案”会使用该范围。</p><button className="inspector-link" disabled={busy} onClick={p.onSeed}>载入教学示例</button></div><details className="inspector-section advanced-scope"><summary>BOS 场景与断面（可选）</summary><label className="inspector-field">场景<input aria-label="BOS 场景" value={scene} disabled={busy} onChange={e=>setScene(e.target.value)}/></label><label className="inspector-field">断面 / 快照<input aria-label="BOS 断面" value={snapshot} disabled={busy} onChange={e=>setSnapshot(e.target.value)}/></label><p className="field-help">真实 BOS 数据源尚未接入；填写名称不会自动取得业务数据。</p></details></>}
  </div><footer>序流 · 可追溯的知识与行动</footer></aside>}
 </div>;
}
