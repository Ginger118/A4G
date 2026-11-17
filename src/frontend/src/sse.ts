export type StreamEvent={event:string;data:any};
/** Fetch POST or GET SSE, including split UTF-8/CRLF frames and EOF validation. */
export async function readEventStream(path:string,body:unknown,signal:AbortSignal,onEvent:(event:StreamEvent)=>void){
 const response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'include',signal,headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
 if(!response.ok){const e=await response.json().catch(()=>({detail:'连接失败'}));throw new Error(typeof e.detail==='string'?e.detail:'请求内容不符合要求');}
 if(!response.body)throw new Error('浏览器未返回可读取的数据流');
 const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',finished=false;
 const consume=(block:string)=>{let event='message';const data:string[]=[];for(const line of block.split(/\r?\n/)){if(line.startsWith('event:'))event=line.slice(6).trim();if(line.startsWith('data:'))data.push(line.slice(5).replace(/^ /,''));}if(!data.length)return;const value=JSON.parse(data.join('\n'));if(event==='error')throw new Error(value.message||'本轮处理未完成');if(event==='done')finished=true;onEvent({event,data:value});};
 try{while(true){const chunk=await reader.read();buffer+=decoder.decode(chunk.value,{stream:!chunk.done});let match;while((match=/\r?\n\r?\n/.exec(buffer))){consume(buffer.slice(0,match.index));buffer=buffer.slice(match.index+match[0].length);}if(chunk.done)break;}if(buffer.trim())consume(buffer);if(!finished)throw new Error('连接提前结束，本轮未完成，可重试');}
 finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}
