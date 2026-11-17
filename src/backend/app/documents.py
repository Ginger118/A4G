"""DAY4/7 text-PDF ingestion, page provenance and private original storage.
Scanned pages are rejected explicitly; OCR/vision require separate verification.
"""
import base64, hashlib, io
from . import storage as store, rag
from .config import settings

class OriginalStore:
    def __init__(self):
        self.backend=settings.object_backend
    def put(self,owner,digest,raw,suffix='.pdf',content_type='application/pdf'):
        key=owner+'/'+digest+suffix
        if self.backend=='minio':
            client=self.client()
            if not client.bucket_exists(settings.minio_bucket):client.make_bucket(settings.minio_bucket)
            client.put_object(settings.minio_bucket,key,io.BytesIO(raw),len(raw),content_type=content_type)
        else:
            path=settings.runtime/'originals'/key;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return key
    def get(self,key):
        if self.backend=='minio':
            response=self.client().get_object(settings.minio_bucket,key)
            try:return response.read()
            finally:response.close();response.release_conn()
        return (settings.runtime/'originals'/key).read_bytes()
    def client(self):
        from minio import Minio
        import os
        return Minio(settings.minio_endpoint,access_key=os.environ.get('AGENT_MINIO_ACCESS_KEY'),secret_key=os.environ.get('AGENT_MINIO_SECRET_KEY'),secure=settings.minio_secure)

def ingest_pdf(owner,name,encoded):
    import pymupdf
    try:raw=base64.b64decode(encoded,validate=True)
    except ValueError:raise ValueError('PDF 编码无效')
    if not raw or len(raw)>10_000_000 or not raw.startswith(b'%PDF-'):raise ValueError('请上传 10MB 内的 PDF')
    digest=hashlib.sha256(raw).hexdigest()
    existing=store.many("SELECT * FROM assets WHERE owner=? AND kind='knowledge'",(owner,))
    for row in existing:
        a=store.public_asset(row)
        if a['metadata'].get('original_sha256')==digest:return a
    try:
        with pymupdf.open(stream=raw,filetype='pdf') as doc:
            if doc.is_encrypted:raise ValueError('暂不支持加密 PDF')
            if not 1<=len(doc)<=100:raise ValueError('PDF 需为 1-100 页')
            pages=[]
            for i,page in enumerate(doc):
                text=page.get_text(sort=True).strip()
                if not text:raise ValueError(f'第 {i+1} 页没有可提取文字，可能是扫描页；本版未启用 OCR，请上传文字型 PDF 或先校对转写')
                pages.append(text)
            if sum(map(len,pages))>2_000_000:raise ValueError('PDF 提取文本过长')
    except ValueError:raise
    except Exception as exc:raise ValueError('PDF 无法解析，请检查文件') from exc
    chunks=[];full='';offset=0
    for page_no,text in enumerate(pages,1):
        if full:full+='\n\n';offset+=2
        for part in rag.splitter.create_documents([text]):
            chunks.append({'id':len(chunks)+1,'text':part.page_content,'offset':offset+part.metadata['start_index'],'page':page_no,'extraction_method':'pymupdf-text'})
        full+=text;offset+=len(text)
    original_store=OriginalStore()
    try:key=original_store.put(owner,digest,raw)
    except Exception as exc:raise ValueError('原文件保存失败，请检查对象存储配置') from exc
    a=rag.publish_knowledge(owner,name,full,{'chunks':chunks,'chunk_count':len(chunks),'chunk_size':rag.CHUNK_SIZE,'overlap':rag.OVERLAP,'splitter':'RecursiveCharacterTextSplitter','vector_store':rag.vector_store_label(),'original_sha256':digest,'doc_version':digest,'pages':len(pages),'extraction_method':'pymupdf-text','original_key':key,'object_backend':original_store.backend})
    return store.public_asset(a)
