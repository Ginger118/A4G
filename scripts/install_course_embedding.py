#!/usr/bin/env python3
"""Pinned public GGUF download and SHA256 verification; local import into Ollama."""
from pathlib import Path
import hashlib,time,subprocess,httpx
ROOT=Path(__file__).resolve().parents[1];cache=ROOT/'.runtime/models';cache.mkdir(parents=True,exist_ok=True)
REPO='ggml-org/embeddinggemma-300M-GGUF'
REVISION='0f741b5a6585bd53aeb15cd1372c56f2a0f65e12'
FILE='embeddinggemma-300M-Q8_0.gguf'
SHA256='b5ce9d77a3fc4b3b39ccb5643c36777911cc4eb46a66962eadfa3f5f60490d63'
SIZE=333590944
target=cache/FILE;url=f'https://huggingface.co/{REPO}/resolve/{REVISION}/{FILE}'
if target.exists() and target.stat().st_size>SIZE:raise SystemExit('缓存大小错误，请检查模型缓存')
start=time.monotonic()
for attempt in range(5):
    pos=target.stat().st_size if target.exists() else 0
    if pos==SIZE:break
    try:
        with httpx.stream('GET',url,headers={'Range':f'bytes={pos}-'},follow_redirects=True,timeout=40) as r:
            r.raise_for_status()
            with target.open('ab' if r.status_code==206 else 'wb') as f:
                for block in r.iter_bytes(1024*1024):
                    f.write(block)
                    if time.monotonic()-start>480:raise TimeoutError('download deadline')
    except (httpx.HTTPError,TimeoutError):
        print('模型下载暂时中断，尝试续传；保留缓存。')
        if time.monotonic()-start>480:break
if not target.exists() or target.stat().st_size!=SIZE or hashlib.sha256(target.read_bytes()).hexdigest()!=SHA256:
    raise SystemExit('模型尚未完整下载或校验不符，未导入；网络恢复后可重试。')
recipe=cache/'Modelfile';recipe.write_text('FROM '+str(target)+'\n')
subprocess.run(['ollama','create','embeddinggemma:300m','-f',str(recipe)],check=True)
print('已校验并导入 EmbeddingGemma Q8_0；课程配置使用此本机别名。')
