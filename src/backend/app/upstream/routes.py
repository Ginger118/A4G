import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from .schemas import UpstreamRequest
from .service import upstream_events
from .. import storage as store
from ..config import settings

def build_router(actor):
    router=APIRouter()
    @router.get('/api/upstream/sessions')
    async def sessions(user=Depends(actor)):
        import json
        rows=store.many('SELECT * FROM upstream_turns WHERE owner=? ORDER BY created DESC LIMIT 100',(user['id'],))
        return [{**r,'response':json.loads(r['response'])} for r in rows]

    @router.post('/api/upstream/stream')
    async def stream(body:UpstreamRequest,request:Request,user=Depends(actor)):
        if body.mode=='live' and not settings.live:raise HTTPException(409,'未配置真实模型；可选择明确标记的规则演示')
        for id in body.document_ids+([body.dataset_id] if body.dataset_id else []):
            try:a=store.get_asset(id,user['id'])
            except ValueError:raise HTTPException(404,'材料不存在或无权访问')
            if id in body.document_ids and a['kind']!='knowledge':raise HTTPException(422,'知识材料类型错误')
            if id==body.dataset_id and (a['kind']!='dataset' or a['metadata'].get('domain')!='power'):raise HTTPException(422,'请选择线路 CSV')
        async def generate():
            try:
                async for event in upstream_events(body,user['id']):
                    if await request.is_disconnected():return
                    yield 'event: '+event['event']+'\ndata: '+store.dumps(event['data'])+'\n\n'
            except asyncio.CancelledError:raise
            except Exception as exc:
                from ..llm import ModelUnavailable
                error=str(exc)[:240] if isinstance(exc,(ValueError,ModelUnavailable)) else '上游处理失败，请重试或检查配置'
                yield 'event: error\ndata: '+store.dumps({'message':error})+'\n\n'
        return StreamingResponse(generate(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    return router
