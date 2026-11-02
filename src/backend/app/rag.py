"""LangChain splitting/retrieval with a transparent local lexical embedding.
Source chunks persist in SQLite; per-user indexes rebuild after restart.
This is not a pretrained semantic embedding model.
"""
import hashlib
import math
import re
import json
from collections import Counter, OrderedDict
from . import storage as store
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
    text=re.sub(r'\s+','',text.lower())
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

def add_document(owner,name,text):
    docs=splitter.create_documents([text])
    chunks=[{'id':i+1,'text':d.page_content,'offset':d.metadata['start_index']} for i,d in enumerate(docs)]
    return store.asset(owner,name,'knowledge',text,{'chunks':chunks,'chunk_count':len(chunks),
        'embedding':'hashed-char-2048-v1','chunk_size':CHUNK_SIZE,'overlap':OVERLAP,
        'splitter':'RecursiveCharacterTextSplitter','splitter_version':SPLITTER_VERSION,
        'vector_store':'LangChain InMemoryVectorStore'})

_indexes=OrderedDict()

def search(owner,query,top_k=4):
    rows=store.many("SELECT * FROM assets WHERE owner=? AND kind='knowledge' ORDER BY id",(owner,))
    if not rows:return []
    signature=tuple((r['id'],hashlib.sha256(r['metadata'].encode()).hexdigest()) for r in rows)
    key=(owner,signature)
    index=_indexes.get(key)
    if index is None:
        index=InMemoryVectorStore(LocalCharacterEmbeddings())
        documents=[]
        for row in rows:
            meta=json.loads(row['metadata'])
            for c in meta['chunks']:
                documents.append(Document(page_content=c['text'],metadata={
                    'document_id':row['id'],'document':row['name'],'chunk_id':c['id'],
                    'sha256':meta['sha256'],'offset':c['offset']}))
        if not documents:return []
        index.add_documents(documents)
        for old in list(_indexes):
            if old[0]==owner:del _indexes[old]
        _indexes[key]=index
        while len(_indexes)>16:_indexes.popitem(last=False)
    _indexes.move_to_end(key)
    results=index.similarity_search_with_score(query,k=top_k)
    return [{**doc.metadata,'text':doc.page_content,'score':round(float(score),4)}
            for doc,score in results if score>0.025]
