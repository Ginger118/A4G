"""Contract tests use explicit doubles. Real services are tested by acceptance script."""
import json,math
import pytest
from app import storage as store,rag
from app.config import settings
from app.embeddings import OllamaSemanticEmbeddings,EmbeddingUnavailable

class Response:
    def __init__(self,data):self.data=data
    def raise_for_status(self):pass
    def json(self):return self.data

def adapter(monkeypatch,vector):
    monkeypatch.setattr('app.embeddings.httpx.get',lambda *a,**kw:Response({'models':[{'name':'teaching-model','digest':'revision-one'}]}))
    monkeypatch.setattr('app.embeddings.httpx.post',lambda *a,**kw:Response({'embeddings':[vector]*len(kw['json']['input'])}))
    return OllamaSemanticEmbeddings('http://127.0.0.1:11434','teaching-model',3)

@pytest.mark.parametrize('vector',[[1,2],[0,0,0],[1,float('nan'),0]])
def test_invalid_vectors_rejected(monkeypatch,vector):
    with pytest.raises(EmbeddingUnavailable):adapter(monkeypatch,vector).embed_query('hello')

def test_semantic_normalization_and_revision(monkeypatch):
    a=adapter(monkeypatch,[3,4,0]);assert a.embed_query('hello')==[0.6,0.8,0]
    assert a.embed_documents(['a','b'])==[[0.6,0.8,0]]*2
    monkeypatch.setattr('app.embeddings.httpx.get',lambda *a,**kw:Response({'models':[{'name':'teaching-model','digest':'revision-two'}]}))
    b=OllamaSemanticEmbeddings('http://127.0.0.1:11434','teaching-model',3)
    assert a.fingerprint!=b.fingerprint

def test_collection_separates_owner_and_embedding():
    from app.repositories.milvus import collection_name
    assert len({collection_name('owner-a','v1'),collection_name('owner-b','v1'),collection_name('owner-a','v2')})==3

def test_failed_index_is_not_published(monkeypatch):
    store.init();monkeypatch.setattr(settings,'vector_backend','milvus')
    def fail(*a,**kw):raise RuntimeError('teaching service down')
    monkeypatch.setattr('app.repositories.milvus.index_documents',fail)
    monkeypatch.setattr('app.repositories.milvus.delete_documents',lambda *a,**kw:None)
    with pytest.raises(ValueError,match='索引保存失败'):rag.add_document('test-course-owner','rollback.md','仅用于测试失败补偿')
    assert not store.many('SELECT * FROM assets WHERE owner=?',('test-course-owner',))

def test_changed_model_requires_explicit_migration(monkeypatch):
    store.init();a=rag.add_document('course-migration','old.md','原始旧资料')
    monkeypatch.setattr(settings,'vector_backend','milvus')
    with pytest.raises(ValueError,match='迁移'):rag.search('course-migration','原始旧资料')
    assert store.get_asset(a['id'],'course-migration')['content']=='原始旧资料'

def test_empty_scope_never_searches_external_store(monkeypatch):
    monkeypatch.setattr(settings,'vector_backend','milvus')
    monkeypatch.setattr('app.embeddings.embedding_info',lambda:pytest.fail('empty scope must stop before connecting'))
    assert rag.search('nobody','question',document_ids=[])==[]
