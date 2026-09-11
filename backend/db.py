"""SQLite persistence, transactions and append-only audit events."""
from __future__ import annotations
import json, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .schema import validate
ROOT=Path(__file__).resolve().parents[1]
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

class Store:
    def __init__(self,path):
        self.path=Path(path).resolve(); self.path.parent.mkdir(parents=True,exist_ok=True)
    @contextmanager
    def connect(self,write=False):
        c=sqlite3.connect(self.path,timeout=15)
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            if write: c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except Exception:
            c.rollback(); raise
        finally: c.close()
    def initialize(self):
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.executescript('''
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('owner','admin','researcher')),researcher_id TEXT NOT NULL DEFAULT '',active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,created REAL NOT NULL,last_seen REAL NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS records(collection TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL,visibility TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created_by TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(collection,id));
            CREATE INDEX IF NOT EXISTS public_records ON records(visibility,collection);
            CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY,path TEXT NOT NULL,original_name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,collection TEXT NOT NULL,record_id TEXT NOT NULL,created_by TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,actor TEXT NOT NULL,action TEXT NOT NULL,collection TEXT NOT NULL,record_id TEXT NOT NULL,before_json TEXT,after_json TEXT,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS trash(collection TEXT NOT NULL,id TEXT NOT NULL,deleted_at TEXT NOT NULL,deleted_by TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('trashed','purged')),PRIMARY KEY(collection,id));
            CREATE TABLE IF NOT EXISTS attempts(key TEXT NOT NULL,at REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS attempts_time ON attempts(key,at);
            ''')
        try: os.chmod(self.path,0o600)
        except OSError: pass
    def seed(self):
        seed=json.loads((ROOT/'data/seed.json').read_text())
        with self.connect(write=True) as c:
            if c.execute('SELECT COUNT(*) FROM records').fetchone()[0]: return
            for collection,items in seed.items():
                for p in items:
                    p=validate(collection,p)
                    c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',(collection,p['id'],json.dumps(p,ensure_ascii=False),p['visibility'],'seed',now()))
    @staticmethod
    def record(row):
        if row is None: return None
        d=json.loads(row['payload']); d.update(_version=row['version'],_updated_at=row['updated_at']); return d
    def get(self,collection,rid):
        with self.connect() as c: return self.record(c.execute('SELECT * FROM records WHERE collection=? AND id=? AND NOT EXISTS(SELECT 1 FROM trash t WHERE t.collection=records.collection AND t.id=records.id)',(collection,rid)).fetchone())
    def list(self,collection,public_only=False):
        with self.connect() as c:
            sql='SELECT * FROM records WHERE collection=? AND NOT EXISTS(SELECT 1 FROM trash t WHERE t.collection=records.collection AND t.id=records.id)'+(" AND visibility='public'" if public_only else '')+' ORDER BY updated_at DESC,id'
            return [self.record(r) for r in c.execute(sql,(collection,))]
    @staticmethod
    def audit(c,actor,action,collection,rid,before=None,after=None):
        c.execute('INSERT INTO audit(actor,action,collection,record_id,before_json,after_json,created_at) VALUES(?,?,?,?,?,?,?)',(actor,action,collection,rid,json.dumps(before,ensure_ascii=False) if before is not None else None,json.dumps(after,ensure_ascii=False) if after is not None else None,now()))
