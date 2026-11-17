const fs=require('fs');const assert=require('node:assert/strict');
const ts=require('typescript');
const source=fs.readFileSync(__dirname+'/../src/sse.ts','utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText;
(async()=>{
 const {readEventStream}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
 function mock(text){const bytes=new TextEncoder().encode(text);global.fetch=async()=>new Response(new ReadableStream({start(c){for(const b of bytes)c.enqueue(new Uint8Array([b]));c.close();}}),{headers:{'Content-Type':'text/event-stream'}});}
 const signal=new AbortController().signal;
 mock('event: answer_delta\r\ndata: {"text":"中文\\n跨块"}\r\n\r\nevent: done\r\ndata: {"status":"ok"}\r\n\r\n');const got=[];
 await readEventStream('/chat/stream',{},signal,e=>got.push(e));assert.equal(got[0].data.text,'中文\n跨块');assert.equal(got.at(-1).event,'done');
 mock('event: answer_delta\ndata: {"text":"partial"}\n\n');await assert.rejects(()=>readEventStream('/chat/stream',{},signal,()=>{}),/提前结束/);
 mock('event: error\ndata: {"message":"teaching failure"}\n\nevent: done\ndata: {}\n\n');const errors=[];await assert.rejects(()=>readEventStream('/chat/stream',{},signal,e=>errors.push(e)),/teaching failure/);assert.equal(errors.length,0);
 console.log('3 frontend SSE protocol checks passed: byte-split UTF-8/CRLF, truncation, terminal error');
})().catch(e=>{console.error(e);process.exit(1)});
