import {useEffect,useState} from 'react';
import './retrieval-demo.css';
type Ref={title:string;sha256:string;retrieved?:boolean};
type Hit={document:string;document_id:string;chunk_id:number;text:string;score:number;headers?:Record<string,string>;page?:number};
type Case={id:string;question:string;rationale:string;references:Ref[];missing_references:string[]};
type Scored=Case&{status:'scored'|'unavailable';recall:number|null;matched_documents:number;expected_documents:number;hits:Hit[]};
type Report={recorded_at:string;elapsed_seconds:number;metric:string;scope:string;summary:{scored_questions:number;total_questions:number;macro_recall:number|null;full_hit_questions:number;partial_hit_questions:number;miss_questions:number};cases:Scored[];retriever:{vector_backend:string;embedding:{model:string}|null;corpus_documents:number}};
type Snapshot={suite:{title:string;label_note:string};cases:Case[];latest:Report|null;stale:boolean};
const pct=(v:number|null)=>v===null?'未评':`${(v*100).toFixed(1)}%`;
export default function RetrievalDemo({request,knowledgeKey,onQuestion}:{request:(path:string,data?:unknown)=>Promise<any>;knowledgeKey:string;onQuestion:(q:string)=>void}){
 const [data,setData]=useState<Snapshot|null>(null),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{let live=true;setLoading(true);request('/evaluation/demo').then(v=>{if(live){setData(v);setError('');}}).catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});return()=>{live=false;};},[request,knowledgeKey]);
 useEffect(()=>{if(!loading&&window.location.hash==='#retrieval-demo')document.getElementById('retrieval-demo')?.scrollIntoView({block:'start'});},[loading]);
 async function run(){setBusy(true);setError('');try{const report:Report=await request('/evaluation/demo/run',{});setData(v=>v?{...v,latest:report,stale:false}:v);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 function download(){if(!data?.latest)return;const u=URL.createObjectURL(new Blob([JSON.stringify(data.latest,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='召回演示结果.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
 const report=data?.latest,summary=report?.summary;
 return <section className="card retrieval-demo" aria-label="召回评估演示" id="retrieval-demo">
  <div className="retrieval-demo-head"><div><span className="retrieval-demo-badge">DEMO · 演示参考集</span><h2>这次检索，找到了哪些依据？</h2><p>{data?.cases.length??8} 道预置问题，运行当前知识库检索后自动计分。参考来源按主题预置，尚未人工审核。</p></div><div className="retrieval-demo-actions"><button className="primary" disabled={busy||loading||!data} onClick={run}>{busy?'正在检索并计分…':'运行召回演示'}</button>{report&&<button className="secondary" onClick={download}>导出结果</button>}</div></div>
  <div className="retrieval-demo-note">计分口径：取前 4 个片段，按文档去重。文档级召回率 = 找到的参考文档数 ÷ 预置参考文档总数；总览取已评题目的平均值。这是演示指标，不代表正式评测成绩或答案准确率。</div>
  {error&&<p className="retrieval-demo-error" role="alert">{error}</p>}
  {loading&&<p role="status">正在读取演示题集…</p>}
  {data?.stale&&<p className="retrieval-demo-error" role="status">知识库或题集已变化，下方是上次运行结果，请重新运行。</p>}
  {summary&&<><div className="retrieval-demo-stats"><div><strong>{pct(summary.macro_recall)}</strong><span>平均文档级召回率 · 前4片段</span></div><div><strong>{summary.scored_questions} / {summary.total_questions}</strong><span>已评题目 · 缺参考版本则未评</span></div><div><strong>{summary.full_hit_questions} / {summary.partial_hit_questions} / {summary.miss_questions}</strong><span>完整命中 / 部分命中 / 未命中</span></div></div><p className="retrieval-demo-meta">上次运行：{new Date(report!.recorded_at).toLocaleString('zh-CN')} · {report!.retriever.vector_backend} · {report!.retriever.embedding?.model||'未执行检索'} · {report!.retriever.corpus_documents} 份知识文档 · {report!.elapsed_seconds} 秒</p></>}
  {data?.cases.map(item=>{const result=report?.cases.find(c=>c.id===item.id);return <details className="retrieval-demo-case" key={item.id}><summary><span className="retrieval-demo-id">{item.id}</span><strong>{item.question}</strong><span className="retrieval-demo-score">{result?`${pct(result.recall)}${result.status==='scored'?` · ${result.matched_documents}/${result.expected_documents}份`:''}`:'待运行'}</span></summary><div className="retrieval-demo-case-body"><p className="retrieval-demo-meta">预置依据：{item.rationale}</p><p><b>参考来源</b>（固定文档版本）</p><ul>{item.references.map(ref=><li key={ref.sha256}>{result?.status==='scored'?(result.references.find(r=>r.sha256===ref.sha256)?.retrieved?'✓ 已找到 · ':'未找到 · '):''}{ref.title}</li>)}</ul>{item.missing_references.length>0&&<p className="retrieval-demo-error">当前账号缺少参考文档版本，此题不会计入平均值：{item.missing_references.join('、')}</p>}{result&&<><p><b>实际返回的前4片段</b>（当前账号全部已入库知识，未按参考答案限制范围）</p>{result.hits.length?result.hits.map((hit,i)=><div className="retrieval-demo-hit" key={i}><strong>{i+1}. {hit.document}</strong><small>片段 {hit.chunk_id} · 相似度 {hit.score.toFixed(4)}{hit.page?` · 第${hit.page}页`:''}</small><p>{hit.text}</p></div>):<p>{result.status==='unavailable'?'缺参考资料，本题未执行检索。':'本次没有超过检索阈值的片段。'}</p>}</>}<button className="secondary" onClick={()=>onQuestion(item.question)}>带入知识问答</button></div></details>;})}
  <p className="retrieval-demo-meta">每次运行仅做检索与统计，不调用回答模型。参考文档命中不代表关键事实完整；后续可在同一题集结构中补充审核标签、片段级标注与独立测试集。</p>
 </section>;
}
