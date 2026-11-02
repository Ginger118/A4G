import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .config import settings

def now():
    return datetime.now(timezone.utc).isoformat()

def uid(prefix):
    return prefix + '_' + secrets.token_hex(6)

def dumps(value):
    return json.dumps(value, ensure_ascii=False, default=str)

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def password_verify(password, stored):
    return secrets.compare_digest(password_hash(password, stored.split(':')[0]), stored)

@contextmanager
def db():
    settings.runtime.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.runtime / 'agent.sqlite3', timeout=20)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    finally:
        con.close()

def one(sql, args=()):
    with db() as con:
        row = con.execute(sql, args).fetchone()
        return dict(row) if row else None

def many(sql, args=()):
    with db() as con:
        return [dict(r) for r in con.execute(sql, args).fetchall()]

def execute(sql, args=()):
    with db() as con:
        con.execute(sql, args)

def init():
    with db() as con:
        con.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id TEXT, expires REAL);
        CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, owner TEXT, name TEXT, kind TEXT, content TEXT, metadata TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, owner TEXT, session_id TEXT, prompt TEXT, mode TEXT, status TEXT, state TEXT, result TEXT, error TEXT, created TEXT, updated TEXT);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, type TEXT, title TEXT, payload TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, owner TEXT, session_id TEXT, role TEXT, content TEXT, created TEXT);
        ''')
        con.execute("UPDATE tasks SET status='interrupted', error='服务重启，任务已中断。可重新提交。' WHERE status IN ('running','pending')")
    # Local-only teaching accounts; do not reuse these credentials on a network deployment.
    for username, role in [('demo', 'user'), ('admin', 'admin'), ('reviewer', 'user')]:
        if not one('SELECT id FROM users WHERE username=?', (username,)):
            execute('INSERT INTO users VALUES(?,?,?,?)', (uid('usr'), username, password_hash('Agent2026!'), role))

def asset(owner, name, kind, content, metadata=None):
    asset_id = uid('ast')
    meta = metadata or {}
    meta['sha256'] = hashlib.sha256(content.encode()).hexdigest()
    execute('INSERT INTO assets VALUES(?,?,?,?,?,?,?)', (asset_id, owner, name, kind, content, dumps(meta), now()))
    return get_asset(asset_id, owner)

def get_asset(asset_id, owner):
    row = one('SELECT * FROM assets WHERE id=? AND owner=?', (asset_id, owner))
    if not row:
        raise ValueError('文件不存在，或当前用户无权访问')
    row['metadata'] = json.loads(row['metadata'])
    return row

def public_asset(row):
    data = dict(row)
    data.pop('content', None)
    if isinstance(data.get('metadata'), str):
        data['metadata'] = json.loads(data['metadata'])
    return data

def event(task_id, event_type, title, payload=None):
    # Persist structured observations, not hidden model reasoning or credentials.
    execute('INSERT INTO events(task_id,type,title,payload,created) VALUES(?,?,?,?,?)',
            (task_id, event_type, title, dumps(payload or {}), now()))

def update_task(task_id, **fields):
    fields['updated'] = now()
    execute('UPDATE tasks SET ' + ','.join(k+'=?' for k in fields) + ' WHERE id=?', tuple(dumps(v) if isinstance(v, (dict,list)) else v for v in fields.values()) + (task_id,))

def list_events(task_id):
    rows = many('SELECT * FROM events WHERE task_id=? ORDER BY seq', (task_id,))
    for row in rows:
        row['payload'] = json.loads(row['payload'])
    return rows
