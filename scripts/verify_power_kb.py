#!/usr/bin/env python3
"""Local acceptance only. Temporary session is memory-only and removed in finally.
Requires the preceding import report; exercises current app endpoints and local RAG.
"""
import hashlib, json, re, secrets, sys, time
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'.course.env',override=True)
import httpx
from app import storage as store, rag

QUERIES=[
 '电路中的集肤效应是什么？',
 'Kron降阶怎样消去非保留节点？',
 'PQ节点、PV节点和平衡节点的已知量是什么？',
 '为什么一次调频是有差调节？',
 '同步发电机次暂态电抗与暂态电抗有什么区别？',
 '数字化变电站GOOSE与SV各传什么数据？',
 '为什么电流互感器CT二次侧禁止开路？',
 '平衡节点的英文是什么？',
 '问答资料中如何解释费兰梯效应？',
]

def main():
    out=ROOT/'evidence/知识库补充20261117';out.mkdir(parents=True,exist_ok=True)
    report=json.loads((out/'首次导入.json').read_text())
    files=[x for x in report['files'] if x['ingest']]
    owner=store.one('SELECT id FROM users WHERE username=?',(report['account'],))['id']
    ids=[f['asset_id'] for f in files]
    token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
    store.execute('INSERT INTO sessions VALUES(?,?,?)',(digest,owner,time.time()+600))
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'scope':'导入完整性与定向链路冒烟，非独立质量评测','retrieval':[],'questions':[]}
    try:
        with httpx.Client(base_url='http://127.0.0.1:8018',cookies={'agent_session':token},timeout=180) as client:
            c=client.get('/api/settings');c.raise_for_status();cfg=c.json()
            result['runtime']={k:cfg[k] for k in ['version','model','provider_host','live_available','vector_store','object_store','embedding']}
            (out/'运行配置核对.json').write_text(json.dumps(result['runtime'],ensure_ascii=False,indent=2))
            print(json.dumps(result['runtime'],ensure_ascii=False),flush=True)
            assert cfg['vector_store']=='Milvus' and cfg['object_store']=='minio', '现有运行服务未使用课程配置'
            assert cfg['provider_host']=='api.deepseek.com' and cfg['live_available'], '需要此前授权的DeepSeek服务'
            status=client.get('/api/knowledge/status');status.raise_for_status();result['stack_status']=status.json()
            assets=client.get('/api/assets');assets.raise_for_status()
            visible={a['id'] for a in assets.json()};assert set(ids)<=visible
            result['http_listed_new_documents']=len(set(ids)&visible)
            assert client.get('/').status_code==200
            result['ui_entry_http']=200
            for f,q in zip(files,QUERIES):
                scoped=rag.search(owner,q,4,[f['asset_id']]);assert scoped
                global_hits=rag.search(owner,q,4,ids)
                result['retrieval'].append({'file':f['file'],'query':q,'scoped_hits':len(scoped),
                    'scoped_headers':[h.get('headers',{}) for h in scoped],
                    'global_top4':[{'document':h['document'],'score':h['score'],'headers':h.get('headers',{})} for h in global_hits]})
            for number,question in [(2,'根据资料，潮流计算中的PQ节点、PV节点和平衡节点各有哪些已知量和待求量？'),(5,'根据资料，GOOSE与SV在数字化变电站中的作用有何区别？')]:
                chosen=files[number]['asset_id'];start=time.perf_counter()
                response=client.post('/api/upstream/stream',json={'question':question,'document_ids':[chosen],
                    'session_id':store.uid('kbcheck'),'mode':'live'})
                response.raise_for_status();events=[]
                for block in response.text.strip().split('\n\n'):
                    lines=block.splitlines();events.append({'event':lines[0][7:],'data':json.loads(lines[1][6:])})
                (out/f'真实问答{number}.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
                assert events[-1]['event']=='done' and events[-1]['data']['status']=='answered', events[-1]
                answer=''.join(e['data']['text'] for e in events if e['event']=='answer_delta')
                sources=[e['data'] for e in events if e['event']=='source']
                assert answer.strip() and re.search(r'\[\d+\]',answer)
                assert sources and all(s['document_id']==chosen for s in sources)
                for source in sources:
                    asset=store.get_asset(chosen,owner)
                    assert asset['content'][source['offset']:source['offset']+len(source['text'])]==source['text']
                item={'question':question,'answer':answer,'sources':len(sources),'scoped_sources':True,
                      'exact_offsets':True,'delta_events':sum(e['event']=='answer_delta' for e in events),
                      'elapsed_seconds':round(time.perf_counter()-start,3)}
                result['questions'].append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
            result['status']='passed'
    finally:
        store.execute('DELETE FROM sessions WHERE token=?',(digest,))
        result['temporary_session_removed']=store.one('SELECT token FROM sessions WHERE token=?',(digest,)) is None
        (out/'验收结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('本地验收完成',flush=True)

if __name__=='__main__':main()
