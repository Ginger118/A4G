"""Milvus course repository. Per-owner and embedding-version collections, explicit scope."""
import hashlib,json
from ..config import settings

def collection_name(owner,fingerprint):
    return 'a4g_v2_'+hashlib.sha256(owner.encode()).hexdigest()[:20]+'_'+fingerprint

def _client():
    from pymilvus import MilvusClient
    return MilvusClient(uri=settings.milvus_uri,timeout=30)

def _id(document):
    m=document.metadata
    return hashlib.sha256(f"{m['document_id']}:{m['chunk_id']}:{m['sha256']}".encode()).hexdigest()

def index_documents(owner,documents,embedding,info):
    if not documents:return
    vectors=embedding.embed_documents([d.page_content for d in documents])
    name=collection_name(owner,info['fingerprint']);client=_client()
    try:
        if not client.has_collection(name):
            client.create_collection(collection_name=name,dimension=info['dimensions'],metric_type='COSINE',auto_id=False,id_type='string',max_length=64,consistency_level='Strong')
        rows=[{'id':_id(d),'vector':v,'document_id':d.metadata['document_id'],'chunk_id':d.metadata['chunk_id'],'text':d.page_content,'source':d.metadata} for d,v in zip(documents,vectors)]
        for start in range(0,len(rows),64):client.upsert(collection_name=name,data=rows[start:start+64])
    finally:client.close()

def delete_documents(owner,document_ids,info):
    client=_client();name=collection_name(owner,info['fingerprint'])
    try:
        if client.has_collection(name):client.delete(collection_name=name,filter='document_id in '+json.dumps(document_ids))
    finally:client.close()

def search_vectors(owner,documents,query_vector,top_k,info):
    from langchain_core.documents import Document
    client=_client();name=collection_name(owner,info['fingerprint'])
    allowed={(d.metadata['document_id'],d.metadata['chunk_id']):d for d in documents}
    ids=sorted({d.metadata['document_id'] for d in documents})
    try:
        if not client.has_collection(name):raise ValueError('当前向量索引不存在，请先执行课程知识库迁移命令')
        hits=client.search(collection_name=name,data=[query_vector],limit=top_k,filter='document_id in '+json.dumps(ids),output_fields=['document_id','chunk_id','text','source'],consistency_level='Strong')[0]
        # SQL-authorized chunks remain authoritative; never expose stale or unowned rows.
        return [(allowed[(h['entity']['document_id'],h['entity']['chunk_id'])],float(h['distance'])) for h in hits if (h['entity']['document_id'],h['entity']['chunk_id']) in allowed]
    finally:client.close()
