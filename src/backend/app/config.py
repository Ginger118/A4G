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
    version: str = '0.2.0'

    @property
    def live(self):
        return bool(self.api_key)

settings = Settings()
