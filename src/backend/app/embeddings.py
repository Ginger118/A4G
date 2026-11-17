"""Course embedding adapter: local Ollama, validated dimensions, model revision identity."""
import hashlib
import math
from functools import lru_cache
import httpx
from langchain_core.embeddings import Embeddings
from .config import settings

class EmbeddingUnavailable(ValueError): pass

class OllamaSemanticEmbeddings(Embeddings):
    def __init__(self, base_url=None, model=None, dimensions=None):
        self.base_url=(base_url or settings.embedding_url).rstrip('/')
        self.model=model or settings.embedding_model
        self.dimensions=dimensions or settings.embedding_dimensions
        try:
            response=httpx.get(self.base_url+'/api/tags',timeout=10);response.raise_for_status()
            models=response.json()['models']
            self.revision=next(m['digest'] for m in models if m['name']==self.model or m.get('model')==self.model)
        except Exception as exc:
            raise EmbeddingUnavailable('嵌入模型未就绪，请检查 Ollama 服务和已下载模型') from exc
        self.fingerprint=hashlib.sha256(f'ollama:{self.model}:{self.revision}:{self.dimensions}:retrieval-v1'.encode()).hexdigest()[:16]

    def _embed(self,texts,query=False):
        if not texts:return []
        output=[]
        try:
            for start in range(0,len(texts),16):
                batch=texts[start:start+16]
                if self.model.startswith('embeddinggemma'):
                    prefix='task: search result | query: ' if query else 'title: none | text: '
                    batch=[prefix+t for t in batch]
                response=httpx.post(self.base_url+'/api/embed',json={'model':self.model,'input':batch,'truncate':False},timeout=120)
                response.raise_for_status();vectors=response.json()['embeddings']
                if len(vectors)!=len(batch):raise ValueError('count')
                for vector in vectors:
                    if len(vector)!=self.dimensions or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vector):raise ValueError('dimension')
                    norm=math.sqrt(sum(v*v for v in vector))
                    if norm<=0:raise ValueError('zero vector')
                    output.append([v/norm for v in vector])
            return output
        except Exception as exc:
            raise EmbeddingUnavailable('语义向量生成失败，请检查模型、向量维度与输入长度') from exc

    def embed_query(self,text):return self._embed([text],query=True)[0]
    def embed_documents(self,texts):return self._embed(texts)

@lru_cache(maxsize=4)
def _semantic(url,model,dimensions):return OllamaSemanticEmbeddings(url,model,dimensions)

def get_embeddings():
    if settings.embedding_backend=='ollama':return _semantic(settings.embedding_url,settings.embedding_model,settings.embedding_dimensions)
    from .rag import LocalCharacterEmbeddings
    return LocalCharacterEmbeddings()

def embedding_info():
    if settings.embedding_backend=='ollama':
        e=get_embeddings()
        return {'backend':'ollama','model':e.model,'revision':e.revision,'dimensions':e.dimensions,'fingerprint':e.fingerprint,'semantic':True}
    return {'backend':'character','model':'hashed-char-2048-v1','dimensions':2048,'fingerprint':'character-v1','semantic':False}
