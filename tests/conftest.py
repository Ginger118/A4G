import os
import sys
import tempfile
from pathlib import Path
os.environ['AGENT_RUNTIME_DIR']=tempfile.mkdtemp(prefix='enterprise-agent-test-')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/backend'))
