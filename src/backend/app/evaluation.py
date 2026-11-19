"""Small frozen-reference retrieval demo; scoring never creates labels from hits.
Runs ordinary authorized RAG with all current-user documents. No answer model calls.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from . import rag, storage as store
from .config import settings

SUITE_PATH = settings.root / 'data/evaluation/recall_demo.json'
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Reference(Strict):
    title: str = Field(min_length=1, max_length=160)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class Case(Strict):
    id: str = Field(min_length=1, max_length=60)
    question: str = Field(min_length=2, max_length=1000)
    references: list[Reference] = Field(min_length=1, max_length=8)
    rationale: str = Field(max_length=600)

class Suite(Strict):
    schema_version: Literal['retrieval-demo.v1']
    suite_id: str
    title: str
    label_status: Literal['demo_unreviewed']
    label_note: str
    top_k: Literal[4]
    metric_unit: Literal['document_over_top4_chunks']
    cases: list[Case] = Field(min_length=1, max_length=20)


def digest(value):
    return hashlib.sha256(store.dumps(value).encode()).hexdigest()


def load_suite():
    suite = Suite.model_validate_json(SUITE_PATH.read_text(encoding='utf-8'))
    if len({c.id for c in suite.cases}) != len(suite.cases):
        raise ValueError('演示题号重复')
    for case in suite.cases:
        if len({r.sha256 for r in case.references}) != len(case.references):
            raise ValueError('同一题参考文档重复')
    return suite


def corpus(owner):
    rows = store.many("SELECT * FROM assets WHERE owner=? AND kind='knowledge' ORDER BY id", (owner,))
    for row in rows:
        row['metadata'] = json.loads(row['metadata'])
    return [r for r in rows if r['metadata'].get('index_status', 'ready') == 'ready']


def corpus_digest(rows):
    # Any additions, removals, text, chunking or index metadata changes invalidate the saved run.
    return digest([(r['id'], r['metadata'], hashlib.sha256(r['content'].encode()).hexdigest()) for r in rows])


def report_path(owner):
    return settings.runtime / 'retrieval-evaluations' / (hashlib.sha256(owner.encode()).hexdigest() + '.json')


def availability(case, rows):
    available = {r['metadata'].get('original_sha256') for r in rows}
    return [r.title for r in case.references if r.sha256 not in available]


def score_case(case, hits, rows):
    expected = {r.sha256 for r in case.references}
    authorized = {r['id']: r for r in rows}
    # Repeated chunks from one document count once; only authoritative SQL versions count.
    found = {authorized[h['document_id']]['metadata'].get('original_sha256')
             for h in hits if h.get('document_id') in authorized}
    matched = expected & found
    missing = availability(case, rows)
    return {'id': case.id, 'question': case.question, 'rationale': case.rationale,
            'references': [r.model_dump() | {'retrieved': r.sha256 in matched} for r in case.references],
            'missing_references': missing, 'status': 'unavailable' if missing else 'scored',
            'matched_documents': len(matched), 'expected_documents': len(expected),
            'recall': None if missing else len(matched) / len(expected), 'hits': hits}


def summarize(cases):
    scored = [c for c in cases if c['status'] == 'scored']
    return {'scored_questions': len(scored), 'total_questions': len(cases),
            'macro_recall': sum(c['recall'] for c in scored) / len(scored) if scored else None,
            'full_hit_questions': sum(c['recall'] == 1 for c in scored),
            'partial_hit_questions': sum(0 < c['recall'] < 1 for c in scored),
            'miss_questions': sum(c['recall'] == 0 for c in scored)}


def snapshot(owner):
    suite = load_suite(); rows = corpus(owner); latest = None
    path = report_path(owner)
    if path.exists():
        latest = json.loads(path.read_text(encoding='utf-8'))
    stale = bool(latest and (latest['suite_digest'] != digest(suite.model_dump()) or
                            latest['corpus_digest'] != corpus_digest(rows)))
    return {'suite': suite.model_dump(), 'cases': [c.model_dump() | {'missing_references': availability(c, rows)} for c in suite.cases],
            'latest': latest, 'stale': stale}


def evaluate(owner):
    with _LOCKS_GUARD:
        lock = _LOCKS.setdefault(owner, threading.Lock())
    if not lock.acquire(blocking=False):
        raise HTTPException(409, '本账号已有召回演示在运行，请稍后查看')
    try:
        suite = load_suite(); rows = corpus(owner); signature = corpus_digest(rows); started = time.perf_counter()
        cases = []
        for case in suite.cases:
            # Missing reference versions are unscored, never an invented 0% or 100%.
            hits = [] if availability(case, rows) else rag.search(owner, case.question, top_k=suite.top_k)
            cases.append(score_case(case, hits, rows))
        if corpus_digest(corpus(owner)) != signature:
            raise HTTPException(409, '知识库在运行期间发生变化，请重新运行演示')
        from .embeddings import embedding_info
        info = embedding_info() if any(c['status'] == 'scored' for c in cases) else None
        report = {'suite_id': suite.suite_id, 'suite_digest': digest(suite.model_dump()), 'corpus_digest': signature,
                  'recorded_at': store.now(), 'label_status': suite.label_status,
                  'scope': '演示参考集；当前用户全部ready知识文档检索；非独立评测或答案准确率',
                  'metric': '文档级召回率：前4片段按文档去重，覆盖参考文档数/参考文档总数',
                  'top_k': suite.top_k, 'summary': summarize(cases), 'cases': cases,
                  'retriever': {'vector_backend': settings.vector_backend, 'embedding': info,
                                'threshold': settings.embedding_threshold if info and info.get('semantic') else .025,
                                'corpus_documents': len(rows)},
                  'elapsed_seconds': round(time.perf_counter() - started, 3)}
        path = report_path(owner); path.parent.mkdir(parents=True, exist_ok=True)
        # Only a complete run replaces the old report. Credentials never enter it.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name); os.chmod(temporary, 0o600)
                stream.write(store.dumps(report))
            os.replace(temporary, path)
        finally:
            if temporary and temporary.exists(): temporary.unlink()
        return report
    finally:
        lock.release()


def build_evaluation_router(actor):
    router = APIRouter()

    @router.get('/api/evaluation/demo')
    async def get_demo(user=Depends(actor)):
        return await asyncio.to_thread(snapshot, user['id'])

    @router.post('/api/evaluation/demo/run')
    async def run_demo(user=Depends(actor)):
        try:
            return await asyncio.to_thread(evaluate, user['id'])
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(503, '召回演示未完成，请检查题集、嵌入与索引服务；上次完整结果保留') from exc
    return router
