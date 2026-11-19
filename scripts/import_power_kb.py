#!/usr/bin/env python3
"""Explicit local course-KB import. Manifest is data; no loader snippets are executed.
Default: preview only. --apply publishes via the app's existing idempotent ingestion.
No credentials, source deletion, global sharing, or splitter override.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def plan(source):
    source = source.resolve()
    manifest_path = source / 'kb_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    rows = manifest.get('documents')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError('清单需包含1-100份资料')
    result = []
    names = set()
    for entry in rows:
        name = entry['file']
        if not isinstance(name, str) or Path(name).name != name or '/' in name or '\\' in name or not name.endswith('.md') or name in names:
            raise ValueError('清单文件名无效或重复')
        names.add(name)
        path = (source / name).resolve()
        if path.parent != source or not path.is_file():
            raise ValueError('资料必须是来源目录内的Markdown文件')
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        if not text.strip() or len(raw) > 2_000_000:
            raise ValueError('资料为空或超过2MB')
        flag = entry.get('ingest_into_vector_db')
        if not isinstance(flag, bool):
            raise ValueError('入库标识必须是布尔值')
        result.append({'file':name, 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw),
                       'ingest':flag, 'text':text, 'doc_id':entry.get('doc_id')})
    return manifest, result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--username', required=True, help='现有本机账号；仅向该账号导入')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--output', type=Path, help='本地证据JSON，默认忽略目录.runtime')
    args = parser.parse_args()
    # Complete source validation before any writes. Source paths are never modified.
    manifest, rows = plan(args.source)
    sys.path.insert(0, str(ROOT / 'src/backend'))
    from dotenv import load_dotenv
    if not (ROOT / '.course.env').is_file():
        raise ValueError('请先按课程手册准备.course.env')
    load_dotenv(ROOT / '.course.env', override=True)
    from app import storage as store, rag
    from app.config import settings
    from app.documents import OriginalStore
    if settings.vector_backend != 'milvus' or settings.object_backend != 'minio' or settings.embedding_backend != 'ollama':
        raise ValueError('需要现有MinIO/Milvus/Ollama课程配置')
    user = store.one('SELECT id FROM users WHERE username=?', (args.username,))
    if not user:
        raise ValueError('账号不存在；先在工作台确认账号')
    result = {'recorded_at':datetime.now(timezone.utc).isoformat(), 'kb_name':manifest.get('kb_name'),
              'mode':'apply' if args.apply else 'preview', 'account':args.username,
              'chunk_size':rag.CHUNK_SIZE, 'overlap':rag.OVERLAP,
              'scope':'本机用户提供资料；未审核电力事实。问答集入库后不能作独立留出评测。', 'files':[]}
    output = args.output or ROOT / '.runtime/power-kb-import.json'
    for row in rows:
        item = {k:v for k,v in row.items() if k != 'text'}
        if not row['ingest']:
            item['status'] = 'reference_only'
        elif not args.apply:
            item['status'] = 'planned'
        else:
            try:
                existing = {r['id'] for r in store.many("SELECT id FROM assets WHERE owner=? AND kind='knowledge'", (user['id'],))}
                asset = rag.add_document(user['id'], row['file'], row['text'])
                meta = asset['metadata']; chunks = meta['chunks']
                assert meta['index_status'] == 'ready'
                assert meta['original_sha256'] == row['sha256']
                assert all(row['text'][c['offset']:c['offset']+len(c['text'])] == c['text'] for c in chunks)
                assert hashlib.sha256(OriginalStore().get(meta['original_key'])).hexdigest() == row['sha256']
                item.update(status='reused' if asset['id'] in existing else 'imported', asset_id=asset['id'],
                            chunks=len(chunks), exact_offsets=True, original_readback=True,
                            header_chunks=sum(bool(c.get('headers')) for c in chunks), splitter_version=meta.get('splitter_version'))
            except Exception as exc:
                item.update(status='failed', error=type(exc).__name__)
                result['files'].append(item)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
                raise
        result['files'].append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
        if args.apply:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'mode':result['mode'], 'selected':sum(r['ingest'] for r in rows),
                      'reference_only':sum(not r['ingest'] for r in rows)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
