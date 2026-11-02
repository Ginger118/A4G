import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('secret_guard',Path(__file__).resolve().parents[1]/'scripts/check_secrets.py')
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

def test_guard_allows_empty_and_placeholder_template():
    assert guard.findings('config/.env.example',b'AGENT_API_KEY=\n')==[]
    assert guard.findings('config/.env.example',b'AGENT_API_KEY=\nAGENT_MODEL=deepseek-flash\n')==[]
    assert guard.findings('config/.env.example',b'AGENT_API_KEY=YOUR_API_KEY\n')==[]

def test_guard_blocks_literal_credential_without_printing_it():
    fake=b'sk-'+b'a'*32
    assert 'provider token' in guard.findings('config/test.py',fake)
    assert guard.findings('config/.env.example',b'AGENT_API_KEY='+fake)

def test_guard_blocks_private_local_files_even_if_force_added():
    for path in ('.runtime/agent.sqlite3','.env','evidence/trace.jsonl','个人材料/report.pdf'):
        assert guard.findings(path,b'local content')
