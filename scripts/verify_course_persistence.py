#!/usr/bin/env python3
"""Run in a NEW process after restarting course storage containers. No document re-embedding."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'.course.env',override=True)
from app import storage as store,rag
from app.embeddings import get_embeddings
from app.documents import OriginalStore
out=ROOT/'evidence/课程栈20261115';summary=json.loads((out/'真实课程验收.json').read_text())
row=store.one('SELECT * FROM assets WHERE id=?',(summary['asset_id'],));a=store.get_asset(row['id'],row['owner'])
def forbidden(*a,**kw):raise AssertionError('Persistent search must NOT re-embed documents')
get_embeddings().embed_documents=forbidden
hits=rag.search(a['owner'],'多久检查一遍设备档案？',4,[a['id']]);assert hits and '十七' in hits[0]['text']
assert OriginalStore().get(a['metadata']['original_key'])==(out/'教学制度.pdf').read_bytes()
result={'status':'passed','new_process':True,'storage_containers_restarted':True,'document_reembedding':False,'original_roundtrip_after_restart':True,'retrieval_after_restart':True}
(out/'重启持久化.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
