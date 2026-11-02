"""Run the built UI and Python API on one local origin. Credentials stay in memory."""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='序流本地 Agent 工作空间')
parser.add_argument('--port',type=int,default=8018)
parser.add_argument('--use-authorized-deepseek-env',action='store_true',
                    help='明确授权后，复用环境中 ANTHROPIC_API_KEY；目的地址固定为 api.deepseek.com')
args=parser.parse_args()
if args.use_authorized_deepseek_env:
    if not os.environ.get('ANTHROPIC_API_KEY'):
        parser.error('现有环境未包含可复用的密钥；请使用项目 .env 配置 AGENT_API_KEY')
    os.environ.setdefault('AGENT_API_KEY',os.environ['ANTHROPIC_API_KEY'])
    os.environ['AGENT_API_BASE']='https://api.deepseek.com'
sys.path.insert(0,str(ROOT/'src/backend'))
if not (ROOT/'src/frontend/dist/index.html').exists():
    parser.error('请先在 src/frontend 中运行 npm install 和 npm run build')
import uvicorn
uvicorn.run('app.main:app',host='127.0.0.1',port=args.port,log_level='warning')
