"""LangChain splitting/retrieval with configurable semantic or lexical embeddings.
Source chunks persist in SQLite; per-user indexes rebuild after restart.
This is not a pretrained semantic embedding model.
"""
import hashlib
import math
import re
import json
from collections import Counter, OrderedDict
from . import storage as store
from .config import settings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

DIMENSIONS=2048
CHUNK_SIZE=420
OVERLAP=60
SPLITTER_VERSION='langchain-recursive-420-60-v1'
splitter=RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,chunk_overlap=OVERLAP,
    separators=['\n\n','\n','。','；','，',' ',''],add_start_index=True)

def embed(text):
    text=text.lower()  # Preserve Latin word boundaries before tokenisation.
    tokens=re.findall(r'[a-z0-9_]+',text)
    chinese=''.join(re.findall(r'[\u4e00-\u9fff]',text))
    tokens+=list(chinese)+[chinese[i:i+2] for i in range(len(chinese)-1)]
    counts=Counter(int(hashlib.sha256(t.encode()).hexdigest()[:8],16)%DIMENSIONS for t in tokens)
    norm=math.sqrt(sum(v*v for v in counts.values())) or 1
    return {str(k):v/norm for k,v in counts.items()}

class LocalCharacterEmbeddings(Embeddings):
    def embed_query(self,text):
        sparse=embed(text)
        return [sparse.get(str(i),0.0) for i in range(DIMENSIONS)]
    def embed_documents(self,texts):return [self.embed_query(t) for t in texts]

def chunk(text):return splitter.split_text(text)

def _documents(rows):
    documents=[]
    for row in rows:
        meta=row['metadata'] if isinstance(row['metadata'],dict) else json.loads(row['metadata'])
        if meta.get('index_status')=='pending':continue
        for c in meta['chunks']:
            documents.append(Document(page_content=c['text'],metadata={
                'document_id':row['id'],'document':row['name'],'chunk_id':c['id'],'headers':c.get('headers',{}),
                'sha256':meta['sha256'],'offset':c['offset'],'page':c.get('page'),
                'doc_version':meta.get('doc_version',meta['sha256']),'extraction_method':c.get('extraction_method','text')}))
    return documents

def publish_knowledge(owner,name,text,metadata):
    from .embeddings import get_embeddings,embedding_info
    info=embedding_info()
    metadata.update(embedding=info['model'],embedding_info=info,vector_store=vector_store_label(),index_status='pending')
    a=store.asset(owner,name,'knowledge',text,metadata)
    try:
        if settings.vector_backend=='milvus':
            from .repositories.milvus import index_documents
            # Pending is private until the durable index is ready.
            ready={**a,'metadata':{**a['metadata'],'index_status':'ready'}}
            index_documents(owner,_documents([ready]),get_embeddings(),info)
        a['metadata']['index_status']='ready'
        store.execute('UPDATE assets SET metadata=? WHERE id=? AND owner=?',(store.dumps(a['metadata']),a['id'],owner))
        return store.get_asset(a['id'],owner)
    except Exception as exc:
        store.execute('DELETE FROM assets WHERE id=? AND owner=?',(a['id'],owner))
        try:
            if settings.vector_backend=='milvus':
                from .repositories.milvus import delete_documents
                delete_documents(owner,[a['id']],info)
        except Exception:pass  # Orphan vectors are inaccessible without an authorized SQL source.
        raise ValueError('知识库索引保存失败，请检查嵌入模型和 Milvus 服务后重试') from exc

def add_document(owner,name,text):
    from .documents import OriginalStore
    from .markdown_chunks import split_markdown,VERSION
    markdown=name.lower().endswith('.md')
    docs=splitter.create_documents([text])
    chunks=split_markdown(text,splitter) if markdown else [{'id':i+1,'text':d.page_content,'offset':d.metadata['start_index']} for i,d in enumerate(docs)]
    raw=text.encode();digest=hashlib.sha256(raw).hexdigest()
    existing=store.many("SELECT * FROM assets WHERE owner=? AND kind='knowledge'",(owner,))
    for row in existing:
        meta=json.loads(row['metadata'])
        if meta.get('original_sha256')==digest and meta.get('index_status','ready')=='ready':return store.get_asset(row['id'],owner)
    original=OriginalStore()
    try:key=original.put(owner,digest,raw,suffix='.txt',content_type='text/plain; charset=utf-8')
    except Exception as exc:raise ValueError('原文件保存失败，请检查对象存储配置') from exc
    return publish_knowledge(owner,name,text,{'chunks':chunks,'chunk_count':len(chunks),
        'chunk_size':CHUNK_SIZE,'overlap':OVERLAP,'splitter':'RecursiveCharacterTextSplitter',
        'splitter_version':VERSION if markdown else SPLITTER_VERSION,'original_sha256':digest,'original_key':key,'object_backend':original.backend})

_indexes=OrderedDict()

def vector_store_label():
    return 'Milvus' if settings.vector_backend=='milvus' else 'LangChain InMemoryVectorStore'

def search(owner,query,top_k=4,document_ids=None):
    from .embeddings import get_embeddings,embedding_info
    rows=store.many("SELECT * FROM assets WHERE owner=? AND kind='knowledge' ORDER BY id",(owner,))
    if document_ids is not None:rows=[r for r in rows if r['id'] in document_ids]
    rows=[r for r in rows if json.loads(r['metadata']).get('index_status')!='pending']
    if not rows:return []
    info=embedding_info();embedding=get_embeddings();documents=_documents(rows)
    if not documents:return []
    if settings.vector_backend=='milvus':
        if any(json.loads(r['metadata']).get('embedding_info',{}).get('fingerprint')!=info['fingerprint'] or json.loads(r['metadata']).get('vector_store')!='Milvus' for r in rows):
            raise ValueError('部分资料尚未迁移到当前语义索引，请先执行课程知识库迁移命令')
        from .repositories.milvus import search_vectors
        results=search_vectors(owner,documents,embedding.embed_query(query),top_k,info)
    else:
        signature=tuple((r['id'],hashlib.sha256(r['metadata'].encode()).hexdigest()) for r in rows)
        key=(owner,signature,info['fingerprint']);index=_indexes.get(key)
        if index is None:
            index=InMemoryVectorStore(embedding);index.add_documents(documents)
            for old in list(_indexes):
                if old[0]==owner:del _indexes[old]
            _indexes[key]=index
            while len(_indexes)>16:_indexes.popitem(last=False)
        _indexes.move_to_end(key);results=index.similarity_search_with_score(query,k=top_k)
    threshold=settings.embedding_threshold if info['semantic'] else 0.025
    return [{**doc.metadata,'text':doc.page_content,'score':round(float(score),4)} for doc,score in results if score>threshold]
