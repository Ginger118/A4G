#!/usr/bin/env python3
"""Resumable migration preserving IDs, old originals and source offsets."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'.course.env',override=True)
from app import storage as store,rag
from app.documents import OriginalStore
from app.embeddings import get_embeddings,embedding_info
from app.repositories.milvus import index_documents
from app.config import settings

def migrate():
    if settings.vector_backend!='milvus' or settings.object_backend!='minio':raise ValueError('迁移需要课程配置')
    info=embedding_info();count=0
    for row in store.many("SELECT * FROM assets WHERE kind='knowledge' ORDER BY id"):
        a=store.get_asset(row['id'],row['owner']);meta=a['metadata']
        if meta.get('index_status')=='pending':continue
        if meta.get('original_key') and meta.get('object_backend','local')=='local':
            raw=(settings.runtime/'originals'/meta['original_key']).read_bytes();suffix=Path(meta['original_key']).suffix
        elif meta.get('original_key') and meta.get('object_backend')=='minio':
            raw=OriginalStore().get(meta['original_key']);suffix=Path(meta['original_key']).suffix
        else:raw=a['content'].encode();suffix='.txt'
        digest=hashlib.sha256(raw).hexdigest()
        key=OriginalStore().put(a['owner'],digest,raw,suffix=suffix,content_type='application/pdf' if suffix=='.pdf' else 'text/plain; charset=utf-8')
        index_documents(a['owner'],rag._documents([a]),get_embeddings(),info)
        meta.update(original_key=key,original_sha256=digest,object_backend='minio',embedding=info['model'],embedding_info=info,vector_store='Milvus',index_status='ready')
        store.execute('UPDATE assets SET metadata=? WHERE id=? AND owner=?',(store.dumps(meta),a['id'],a['owner']));count+=1
    print(json.dumps({'migrated':count,'model':info['model'],'dimensions':info['dimensions'],'scope':'knowledge only; original files and IDs preserved'},ensure_ascii=False))
if __name__=='__main__':migrate()
