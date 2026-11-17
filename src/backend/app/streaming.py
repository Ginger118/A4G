"""SSE transport for live chat and durable analysis events."""
import asyncio,json
from contextlib import aclosing
from typing import Literal
from pydantic import BaseModel,Field,ConfigDict
from fastapi import APIRouter,Depends,HTTPException,Request
from fastapi.responses import StreamingResponse
from . import storage as store,llm
from .config import settings
from .memory import select_context,CHAT_SYSTEM

class ChatInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question:str=Field(min_length=1,max_length=6000)
    session_id:str=Field(default='',max_length=100,pattern=r'^[a-zA-Z0-9_-]*$')
    mode:Literal['live','demo']='live'

def encode(event,data):return 'event: '+event+'\ndata: '+store.dumps(data)+'\n\n'

async def chat_events(body,owner):
    session=body.session_id or store.uid('session');task_id=store.uid('task');answer='';finished=False
    history,context_info=select_context(owner,session,body.question)
    state={'task_type':'chat','step':0,'transport':'model_stream','context':context_info}
    store.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)',(task_id,owner,session,body.question,body.mode,'running',store.dumps(state),'','',store.now(),store.now()))
    store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),owner,session,'user',body.question,store.now()))
    try:
        yield {'event':'session','data':{'session_id':session,'task_id':task_id}}
        yield {'event':'step','data':{'stage':'model','status':'running'}}
        store.event(task_id,'context_selected','会话上下文已选择',context_info)
        if body.mode=='demo':
            answer='当前为本地规则演示，未调用 AI 模型。切换真实模型后可进行流式对话；也可以使用任务理解或工具分析体验本地能力。'
            yield {'event':'answer_delta','data':{'text':answer}}
        else:
            messages=[{'role':'system','content':CHAT_SYSTEM}]+history+[{'role':'user','content':body.question}]
            async with aclosing(llm.stream_completion(messages)) as chunks:
                async for delta in chunks:
                    answer+=delta
                    yield {'event':'answer_delta','data':{'text':delta}}
            if not answer.strip():raise ValueError('模型未返回有效内容')
        store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),owner,session,'assistant',answer,store.now()))
        state['chat_completed']=True
        store.update_task(task_id,status='succeeded',state=state,result=answer)
        store.event(task_id,'model_completed','流式对话完成',{'transport':'ChatDeepSeek.astream'})
        finished=True
        yield {'event':'done','data':{'session_id':session,'task_id':task_id,'status':'succeeded'}}
    except (asyncio.CancelledError,GeneratorExit):
        raise
    except Exception as exc:
        message=str(exc)[:240] if isinstance(exc,(ValueError,llm.ModelUnavailable)) else '对话处理失败，请重试'
        store.update_task(task_id,status='failed',result=answer,error=message)
        store.event(task_id,'task_failed','流式对话失败',{'message':message})
        finished=True
        yield {'event':'error','data':{'message':message}}
    finally:
        if not finished:
            store.update_task(task_id,status='cancelled',result=answer,error='用户停止或连接中断；部分回复不作为完整答案')
            store.event(task_id,'task_cancelled','流式对话已停止')


def build_stream_router(actor):
    router=APIRouter()
    @router.post('/api/chat/stream')
    async def chat(body:ChatInput,request:Request,user=Depends(actor)):
        if not body.question.strip():raise HTTPException(422,'请输入问题')
        if body.mode=='live' and not settings.live:raise HTTPException(409,'未配置真实模型')
        if store.one("SELECT id FROM tasks WHERE owner=? AND status IN ('pending','running')",(user['id'],)):raise HTTPException(409,'当前已有任务执行中，请等待或停止')
        async def generate():
            async with aclosing(chat_events(body,user['id'])) as events:
                async for e in events:
                    if await request.is_disconnected():return
                    yield encode(e['event'],e['data'])
        return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})

    @router.get('/api/tasks/{task_id}/events')
    async def events(task_id:str,request:Request,user=Depends(actor)):
        def task():return store.one('SELECT * FROM tasks WHERE id=? AND owner=?',(task_id,user['id']))
        if not task():raise HTTPException(404,'任务不存在或无权访问')
        async def generate():
            cursor=0
            while True:
                if await request.is_disconnected():return
                rows=store.many('SELECT * FROM events WHERE task_id=? AND seq>? ORDER BY seq',(task_id,cursor))
                for row in rows:
                    cursor=row['seq'];payload=json.loads(row['payload'])
                    if row['type']=='answer_delta':yield encode('answer_delta',payload)
                    else:yield encode('step',{'stage':row['type'],'title':row['title'],'payload':payload,'seq':cursor})
                t=task()
                if t['status'] not in ('pending','running'):
                    # Drain deltas committed between the event read and final state read.
                    trailing=store.many("SELECT * FROM events WHERE task_id=? AND seq>? ORDER BY seq",(task_id,cursor))
                    for row in trailing:
                        cursor=row['seq'];payload=json.loads(row['payload'])
                        yield encode('answer_delta' if row['type']=='answer_delta' else 'step',payload if row['type']=='answer_delta' else {'stage':row['type'],'title':row['title'],'payload':payload,'seq':cursor})
                    if t['status'] in ('failed','cancelled','interrupted'):yield encode('error',{'message':t['error'] or '任务已停止','status':t['status']});return
                    state=json.loads(t['state']);content=t['result']
                    if state.get('report_id'):content=store.get_asset(state['report_id'],user['id'])['content']
                    yield encode('answer_final',{'text':content})
                    yield encode('done',{'status':t['status'],'task_id':task_id,'state':state});return
                await asyncio.sleep(.15)
        return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    return router
