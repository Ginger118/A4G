import asyncio
import json
from . import storage as store,llm

async def run_chat_task(task_id):
    task=store.one('SELECT * FROM tasks WHERE id=?',(task_id,))
    state=json.loads(task['state'])
    store.update_task(task_id,status='running')
    store.event(task_id,'model_started','多轮对话 · LangChain',{'adapter':'ChatDeepSeek','history_messages':len(state.get('conversation',[]))})
    try:
        if task['mode']=='live':
            messages=[{'role':'system','content':'你是序流电力知识与辅助分析助手。用通俗中文回答，保留上下文。也可以处理一般问题。'
                '普通对话没有检索知识库、读取文件或执行工具，不能假装完成这些操作；需要时提示切换知识库或工具分析。'
                '不确定时说明，不编造规程或执行结果。'}]
            messages+=state.get('conversation',[])
            messages.append({'role':'user','content':task['prompt']})
            message,usage=await llm.completion(messages)
            answer=message.get('content') or ''
            if not answer.strip():raise ValueError('模型没有返回对话内容')
        else:
            answer='当前是本地规则演示，不提供模拟的 AI 对话。切换真实模型后可进行多轮聊天；也可在工具分析中体验真实代码统计。'
            usage={}
        store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),task['owner'],task['session_id'],'assistant',answer,store.now()))
        state['chat_completed']=True
        store.update_task(task_id,status='succeeded',state=state,result=answer)
        store.event(task_id,'model_completed','对话完成',{'usage':usage,'adapter':'ChatDeepSeek','mode':task['mode']})
    except asyncio.CancelledError:
        store.update_task(task_id,status='interrupted',error='对话已中断');raise
    except Exception as exc:
        error=str(exc) if isinstance(exc,(ValueError,llm.ModelUnavailable)) else '对话服务异常，请稍后重试'
        store.update_task(task_id,status='failed',error=error)
        store.event(task_id,'task_failed','对话未完成',{'error':error})
