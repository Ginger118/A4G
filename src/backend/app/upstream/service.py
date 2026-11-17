"""DAY11 SSE stages + DAY9.5 SQLite checkpoints, isolated by authenticated owner."""
import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from .graph import build_upstream_graph
from .. import storage as store
from ..config import settings

async def upstream_events(body,owner):
    session_id=body.session_id or store.uid('upstream')
    request_id=store.uid('request')
    thread_id=owner+':'+session_id+':'+request_id
    settings.runtime.mkdir(parents=True,exist_ok=True)
    yield {'event':'session','data':{'session_id':session_id,'request_id':request_id,'mode':body.mode}}
    async with AsyncSqliteSaver.from_conn_string(str(settings.runtime/'upstream-checkpoints.sqlite3')) as saver:
        graph=build_upstream_graph(saver)
        config={'configurable':{'thread_id':thread_id},'recursion_limit':16}
        last=store.one('SELECT response FROM upstream_turns WHERE owner=? AND session_id=? ORDER BY created DESC LIMIT 1',(owner,session_id))
        import json
        previous=json.loads(last['response'])['contract'] if last else {}
        # Explicit current scope replaces old scope, preventing stale snapshot reuse.
        state={**body.model_dump(),'owner':owner,'request_id':request_id,'session_id':session_id,'previous':{'goal':previous.get('goal',{}),'scope':previous.get('scope',{})},'intent':{},'scope':{},'missing_fields':[],'evidence':[],'plan_steps':[],'answer':'','contract':{}}
        streamed=False
        async for part in graph.astream(state,config,stream_mode=['updates','custom'],version='v2'):
            if part['type']=='custom':
                streamed=True
                yield part['data']
                continue
            for node,values in part['data'].items():
                state.update(values)
                yield {'event':'step','data':{'stage':node,'status':'completed'}}
                if node=='recall':
                    for hit in state['evidence']:yield {'event':'source','data':hit}
        contract=state['contract']
        if contract['status']=='needs_clarification':yield {'event':'clarification','data':{'missing_fields':contract['missing_fields']}}
        if not streamed and state['answer']:
            yield {'event':'answer_delta','data':{'text':state['answer']}}
        store.execute('INSERT INTO upstream_turns VALUES(?,?,?,?,?,?)',(request_id,owner,session_id,body.question,store.dumps({'answer':state['answer'],'contract':contract,'sources':state['evidence']}),store.now()))
        yield {'event':'plan','data':contract}
        yield {'event':'done','data':{'status':contract['status'],'session_id':session_id,'execution_authorized':False}}
