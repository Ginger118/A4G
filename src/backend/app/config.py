from pathlib import Path
from dataclasses import dataclass
import os
import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / '.env', override=False)
if (ROOT / '.vendor').exists():
    sys.path.insert(0, str(ROOT / '.vendor'))
os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'

@dataclass
class Settings:
    root: Path = ROOT
    runtime: Path = Path(os.environ.get('AGENT_RUNTIME_DIR', str(ROOT / '.runtime')))
    api_base: str = os.environ.get('AGENT_API_BASE', 'https://api.deepseek.com').rstrip('/')
    api_key: str = os.environ.get('AGENT_API_KEY', '')
    model: str = os.environ.get('AGENT_MODEL', 'deepseek-flash')
    vision_model: str = os.environ.get('AGENT_VISION_MODEL', 'deepseek-flash')
    max_steps: int = 12
    tool_timeout: int = 120
    version: str = '0.6.0'
    vector_backend: str = os.environ.get('AGENT_VECTOR_BACKEND','memory')
    milvus_uri: str = os.environ.get('AGENT_MILVUS_URI','http://127.0.0.1:19530')
    object_backend: str = os.environ.get('AGENT_OBJECT_BACKEND','local')
    minio_endpoint: str = os.environ.get('AGENT_MINIO_ENDPOINT','127.0.0.1:9000')
    minio_bucket: str = os.environ.get('AGENT_MINIO_BUCKET','a4g-originals')
    minio_secure: bool = os.environ.get('AGENT_MINIO_SECURE','true').lower()=='true'

    embedding_backend: str = os.environ.get('AGENT_EMBEDDING_BACKEND','character')
    embedding_url: str = os.environ.get('AGENT_EMBEDDING_URL','http://127.0.0.1:11434')
    embedding_model: str = os.environ.get('AGENT_EMBEDDING_MODEL','embeddinggemma:300m')
    embedding_dimensions: int = int(os.environ.get('AGENT_EMBEDDING_DIMENSIONS','768'))
    embedding_threshold: float = float(os.environ.get('AGENT_EMBEDDING_THRESHOLD','0.30'))

    chat_context_budget: int = int(os.environ.get('AGENT_CHAT_CONTEXT_BUDGET','24000'))

    @property
    def live(self):
        return bool(self.api_key)

settings = Settings()

if settings.vector_backend not in ('memory','milvus'): raise ValueError('未知向量后端')
if settings.object_backend not in ('local','minio'): raise ValueError('未知对象存储后端')

if settings.embedding_backend not in ('character','ollama'): raise ValueError('未知嵌入后端')
