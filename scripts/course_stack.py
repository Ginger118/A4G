#!/usr/bin/env python3
"""Isolated course services; credentials are local, volumes are never removed."""
import argparse,os,secrets,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('action',choices=['init','up','stop','status']);a=p.parse_args()
env=ROOT/'.course.env'
if a.action=='init':
    if env.exists():print('课程配置已存在，保留原值。')
    else:
        content='\n'.join(['AGENT_VECTOR_BACKEND=milvus','AGENT_OBJECT_BACKEND=minio','AGENT_MILVUS_URI=http://127.0.0.1:19538','AGENT_MINIO_ENDPOINT=127.0.0.1:19100','AGENT_MINIO_BUCKET=a4g-originals','AGENT_MINIO_SECURE=false','AGENT_MINIO_ACCESS_KEY=a4g'+secrets.token_hex(8),'AGENT_MINIO_SECRET_KEY='+secrets.token_urlsafe(32),'AGENT_EMBEDDING_BACKEND=ollama','AGENT_EMBEDDING_URL=http://127.0.0.1:11434','AGENT_EMBEDDING_MODEL=embeddinggemma:300m','AGENT_EMBEDDING_DIMENSIONS=768','AGENT_EMBEDDING_THRESHOLD=0.30',''])
        fd=os.open(env,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(content)
        print('已生成本机课程配置（私密文件，不提交）。')
else:
    if not env.exists():p.error('先运行 init')
    cmd=['docker','compose','--env-file',str(env),'-f',str(ROOT/'docker/course-compose.yaml')]
    cmd+= {'up':['up','-d'],'stop':['stop'],'status':['ps']}[a.action]
    subprocess.run(cmd,cwd=ROOT,check=True)
