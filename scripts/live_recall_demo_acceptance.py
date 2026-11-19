#!/usr/bin/env python3
"""Local-only HTTP acceptance; no saved password or session token; no answer calls."""
import hashlib,json,re,secrets,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/backend'))
import httpx
from app import storage as store
OUT=ROOT/'evidence/召回演示20261117';OUT.mkdir(parents=True,exist_ok=True)

def main():
    results={};tokens=[]
    try:
        assert httpx.get('http://127.0.0.1:8018/api/evaluation/demo').status_code==401
        for account in ['demo','reviewer']:
            owner=store.one('SELECT id FROM users WHERE username=?',(account,))['id']
            token=secrets.token_urlsafe(32);hashed=hashlib.sha256(token.encode()).hexdigest();tokens.append(hashed)
            store.execute('INSERT INTO sessions VALUES(?,?,?)',(hashed,owner,time.time()+600))
            with httpx.Client(base_url='http://127.0.0.1:8018',cookies={'agent_session':token},timeout=180) as client:
                before=client.get('/api/evaluation/demo');before.raise_for_status();snapshot=before.json();assert len(snapshot['cases'])==8
                r=client.post('/api/evaluation/demo/run',json={});r.raise_for_status();report=r.json()
                (OUT/f'{account}-真实结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
                rows=store.many("SELECT id,metadata FROM assets WHERE owner=? AND kind='knowledge'",(owner,))
                hashes={r['id']:json.loads(r['metadata']).get('original_sha256') for r in rows}
                independently=[]
                for case in report['cases']:
                    assert len(case['hits'])<=4
                    assert all(h['document_id'] in hashes for h in case['hits'])
                    if case['status']=='scored':
                        expected={r['sha256'] for r in case['references']};actual={hashes[h['document_id']] for h in case['hits']}
                        recall=len(expected&actual)/len(expected);assert recall==case['recall'];independently.append(recall)
                    else:assert case['recall'] is None and case['missing_references']
                assert report['summary']['macro_recall']==(sum(independently)/len(independently) if independently else None)
                saved=client.get('/api/evaluation/demo').json();assert saved['latest']==report and saved['stale'] is False
                if account=='demo':
                    assert report['retriever']['vector_backend']=='milvus' and len(independently)==8
                    ui=client.get('/?view=knowledge');ui.raise_for_status()
                    js=re.search(r'<script[^>]+src="([^"]+)"',ui.text).group(1)
                    assert '运行召回演示' in client.get(js).text
                else:
                    assert not independently and report['summary']['macro_recall'] is None
                results[account]={'summary':report['summary'],'cases':[{'id':c['id'],'question':c['question'],'recall':c['recall'],'matched':c['matched_documents'],'expected':c['expected_documents'],'hits':len(c['hits'])} for c in report['cases']],
                                  'retriever':report['retriever'],'elapsed_seconds':report['elapsed_seconds'],'saved_roundtrip':True,'independent_recount':True,'owner_scope':True}
        results['unauthenticated_status']=401;results['ui_bundle_http']=200;results['scope']='真实Milvus/Ollama检索，对固定未审核文档参考自动计分；无回答模型调用、无正式准确率结论'
    finally:
        for hashed in tokens:store.execute('DELETE FROM sessions WHERE token=?',(hashed,))
        results['temporary_sessions_removed']=all(store.one('SELECT token FROM sessions WHERE token=?',(h,)) is None for h in tokens)
        (OUT/'真实验收摘要.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps({'demo':results['demo']['summary'],'reviewer':results['reviewer']['summary'],'temporary_sessions_removed':results['temporary_sessions_removed']},ensure_ascii=False))
if __name__=='__main__':main()
