import asyncio
import json
from collections import Counter
from .contracts import PlanningContext
from .executor import Executor
from .planners.llm_tool_calling import LLMToolCallingPlanner
from .planners.demo import DemoPlanner
from ..config import settings
from .. import storage as store

PLANNERS = {'live': LLMToolCallingPlanner, 'demo': DemoPlanner}

async def run_task(task_id, registry):
    task=store.one('SELECT * FROM tasks WHERE id=?',(task_id,))
    context=PlanningContext(task_id,task['owner'],task['prompt'],task['mode'],json.loads(task['state']),[],registry.available_specs())
    planner=PLANNERS[task['mode']]()
    executor=Executor(registry)
    store.update_task(task_id,status='running')
    store.event(task_id,'task_started','开始处理任务',{'planner':type(planner).__name__,'model':settings.model if task['mode']=='live' else None,
        'version':settings.version,'prompt_version':'power-assistant-v1' if context.state.get('business')=='power' else 'feedback-planner-v1','max_steps':settings.max_steps,
        'framework':'LangChain','model_adapter':'ChatDeepSeek',
        'goal':task['prompt'],'input_id':context.state.get('input_id'),
        'input_sha256':context.state.get('input_sha256'),
        'model_parameters':{'temperature':0.2,'thinking':'disabled'},
        'retrieval':{'embedding':'hashed-char-2048-v1','splitter':'RecursiveCharacterTextSplitter','vector_store':'InMemoryVectorStore','chunk_size':420,'overlap':60},
        'tools':[{'id':t.tool_id,'version':t.version,'input_schema':t.input_model.model_json_schema(),
                  'output_schema':t.output_schema,'permission':t.permission,'timeout':t.timeout} for t in context.tools]})
    failures=Counter(); used=0
    try:
        for step in range(settings.max_steps):
            if store.one('SELECT status FROM tasks WHERE id=?',(task_id,))['status']=='cancelled':
                store.event(task_id,'task_cancelled','任务已取消'); return
            context.state['step']=used
            store.event(task_id,'planner_started','正在选择下一步',{'step':step+1})
            decision=await planner.decide(context)
            store.event(task_id,'planner_decision','规划器返回决策',{'kind':decision.kind,'message':decision.message,
                'tools':[c.tool_id for c in decision.calls],'usage':decision.usage})
            if decision.kind in ('finish','ask_user'):
                if decision.kind=='finish' and context.state.get('report_id'):
                    report=store.get_asset(context.state['report_id'],context.owner)
                    if report['kind']!='report' or not report['metadata'].get('verified'):
                        raise ValueError('最终产物核验未通过')
                    store.update_task(task_id,status='succeeded',state=context.state,result=decision.message)
                    store.event(task_id,'task_completed','任务完成 · 产物已验证',{'report_id':report['id'],'verification':report['metadata']['verified']})
                else:
                    store.update_task(task_id,status='waiting_input',state=context.state,result=decision.message)
                    store.event(task_id,'waiting_input','需要补充信息',{'message':decision.message})
                store.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(store.uid('msg'),context.owner,task['session_id'],'assistant',decision.message,store.now()))
                return
            if not decision.calls: raise ValueError('规划器未提供可执行动作')
            for call in decision.calls:
                if used>=settings.max_steps: raise ValueError('已达到最大工具调用次数，任务已停止')
                if store.one('SELECT status FROM tasks WHERE id=?',(task_id,))['status']=='cancelled': return
                result=await executor.execute(call,context)
                used+=1
                if not result.success:
                    failures[call.tool_id]+=1
                    if failures[call.tool_id]>=3: raise ValueError('同一工具连续修正仍失败，任务已停止：'+(result.error or ''))
                else: failures[call.tool_id]=0
                context.history.append({'role':'tool','tool_call_id':call.call_id,'content':store.dumps(result.model_dump())})
                store.update_task(task_id,state=context.state)
        raise ValueError('已达到最大规划轮数，任务已停止')
    except asyncio.CancelledError:
        store.update_task(task_id,status='interrupted',error='服务停止，任务被中断',state=context.state)
        raise
    except Exception as exc:
        from ..llm import ModelUnavailable
        error=str(exc)[:300] if isinstance(exc,(ValueError,ModelUnavailable)) else '任务执行异常，请检查工具轨迹后重试。'
        store.update_task(task_id,status='failed',error=error,state=context.state)
        store.event(task_id,'task_failed','任务未完成',{'error':error})
