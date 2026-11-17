"""Authenticated course readiness; probes configured backends, never exposes credentials."""
from .config import settings

def inspect_stack():
    result={'vector_backend':settings.vector_backend,'object_backend':settings.object_backend,'embedding_backend':settings.embedding_backend,'services':{}}
    try:
        from .embeddings import embedding_info,get_embeddings
        info=embedding_info();v=get_embeddings().embed_query('课程连接检查')
        result['embedding']=info;result['services']['embedding']={'ready':True,'dimensions':len(v)}
    except Exception:result['services']['embedding']={'ready':False,'message':'嵌入服务未就绪'}
    try:
        if settings.object_backend=='minio':
            from .documents import OriginalStore
            client=OriginalStore().client();exists=client.bucket_exists(settings.minio_bucket)
            result['services']['objects']={'ready':True,'bucket_exists':exists}
        else:result['services']['objects']={'ready':True,'mode':'local'}
    except Exception:result['services']['objects']={'ready':False,'message':'对象存储未就绪'}
    try:
        if settings.vector_backend=='milvus':
            from .repositories.milvus import _client
            client=_client()
            try:client.list_collections()
            finally:client.close()
        result['services']['vectors']={'ready':True,'mode':settings.vector_backend}
    except Exception:result['services']['vectors']={'ready':False,'message':'向量存储未就绪'}
    result['ready']=all(s['ready'] for s in result['services'].values())
    return result
