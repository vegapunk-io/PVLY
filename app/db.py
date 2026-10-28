"""SQLite persistence (prototype). Swap for Postgres via SQLAlchemy when scaling; the schema is deliberately flat."""
import json
import sqlite3
import threading
import time
from contextlib import contextmanager

from . import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
  id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  status TEXT NOT NULL,            -- queued | running | done | error
  modality TEXT,
  filename TEXT,
  mime TEXT,
  size INTEGER,
  sha256 TEXT,
  hash_only INTEGER DEFAULT 0,
  blob_path TEXT,
  blob_expires_at REAL,
  error TEXT,
  report_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at DESC);
CREATE TABLE IF NOT EXISTS removals (
  id TEXT PRIMARY KEY,
  scan_id TEXT NOT NULL,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  status TEXT NOT NULL,            -- queued | running | done | error
  modality TEXT,
  attested INTEGER DEFAULT 0,
  input_sha256 TEXT,
  output_sha256 TEXT,
  output_blob_path TEXT,
  output_blob_expires_at REAL,
  fields_removed TEXT,             -- JSON list
  report_json TEXT,
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_removals_created ON removals(created_at DESC);
CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  status TEXT NOT NULL,
  preset TEXT,
  attested INTEGER DEFAULT 0,
  scan_ids TEXT,
  removal_ids TEXT,
  output_blob_path TEXT,
  output_blob_expires_at REAL,
  report_json TEXT,
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_batches_created ON batches(created_at DESC);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL, scan_id TEXT, kind TEXT, detail TEXT
);
"""


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(SCHEMA)


def create_scan(scan_id, modality, filename, mime, size, sha256, hash_only, blob_path):
    now = time.time()
    expires = None if hash_only or not blob_path else now + config.BLOB_TTL_HOURS * 3600
    with _lock, conn() as c:
        c.execute(
            "INSERT INTO scans(id,created_at,updated_at,status,modality,filename,mime,size,sha256,hash_only,blob_path,blob_expires_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (scan_id, now, now, "queued", modality, filename, mime, size, sha256, int(hash_only), blob_path, expires))
        c.execute("INSERT INTO events(ts,scan_id,kind,detail) VALUES(?,?,?,?)", (now, scan_id, "created", filename))


def set_status(scan_id, status, error=None):
    with _lock, conn() as c:
        c.execute("UPDATE scans SET status=?, error=?, updated_at=? WHERE id=?", (status, error, time.time(), scan_id))


def save_report(scan_id, report: dict):
    with _lock, conn() as c:
        c.execute("UPDATE scans SET status='done', report_json=?, updated_at=? WHERE id=?",
                  (json.dumps(report), time.time(), scan_id))


def clear_blob(scan_id):
    with _lock, conn() as c:
        c.execute("UPDATE scans SET blob_path=NULL, blob_expires_at=NULL WHERE id=?", (scan_id,))


def get_scan(scan_id):
    with conn() as c:
        row = c.execute("SELECT * FROM scans WHERE id=?", (scan_id,)).fetchone()
        return dict(row) if row else None


def list_scans(limit=25):
    with conn() as c:
        rows = c.execute("SELECT id,created_at,status,modality,filename,mime,size,sha256,report_json FROM scans"
                         " ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            rep = json.loads(d.pop("report_json") or "{}")
            d["conclusion"] = (rep.get("conclusion") or {}).get("provenance_class")
            d["evidence_grade"] = (rep.get("conclusion") or {}).get("evidence_grade")
            out.append(d)
        return out


def expired_blobs(now=None):
    now = now or time.time()
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id, blob_path FROM scans WHERE blob_path IS NOT NULL AND blob_expires_at IS NOT NULL AND blob_expires_at < ?",
            (now,)).fetchall()]


def stats():
    with conn() as c:
        total = c.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        done = c.execute("SELECT COUNT(*) FROM scans WHERE status='done'").fetchone()[0]
        rtotal = c.execute("SELECT COUNT(*) FROM removals").fetchone()[0]
        rdone = c.execute("SELECT COUNT(*) FROM removals WHERE status='done'").fetchone()[0]
        return {"scans_total": total, "scans_done": done,
                "removals_total": rtotal, "removals_done": rdone}


def create_removal(removal_id, scan_id, modality, input_sha256, attested):
    now = time.time()
    expires = now + config.BLOB_TTL_HOURS * 3600
    with _lock, conn() as c:
        c.execute(
            "INSERT INTO removals(id,scan_id,created_at,updated_at,status,modality,attested,input_sha256,output_blob_expires_at)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (removal_id, scan_id, now, now, "queued", modality, int(attested), input_sha256, expires))
    return removal_id


def set_removal_status(removal_id, status, error=None):
    with _lock, conn() as c:
        c.execute("UPDATE removals SET status=?, error=?, updated_at=? WHERE id=?",
                  (status, error, time.time(), removal_id))


def save_removal_result(removal_id, output_sha256, output_blob_path, fields_removed, report):
    now = time.time()
    with _lock, conn() as c:
        c.execute(
            "UPDATE removals SET status='done', output_sha256=?, output_blob_path=?, fields_removed=?, report_json=?, updated_at=? WHERE id=?",
            (output_sha256, output_blob_path, json.dumps(fields_removed), json.dumps(report), now, removal_id))


def get_removal(removal_id):
    with conn() as c:
        row = c.execute("SELECT * FROM removals WHERE id=?", (removal_id,)).fetchone()
        return dict(row) if row else None


def expired_removal_blobs(now=None):
    now = now or time.time()
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id, output_blob_path FROM removals WHERE output_blob_path IS NOT NULL AND output_blob_expires_at IS NOT NULL AND output_blob_expires_at < ?",
            (now,)).fetchall()]


def create_batch(batch_id, scan_ids, preset, attested):
    now = time.time()
    expires = now + config.BLOB_TTL_HOURS * 3600
    with _lock, conn() as c:
        c.execute(
            "INSERT INTO batches(id,created_at,updated_at,status,preset,attested,scan_ids,output_blob_expires_at)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (batch_id, now, now, "queued", preset, int(attested), json.dumps(scan_ids), expires))


def set_batch_status(batch_id, status, error=None):
    with _lock, conn() as c:
        c.execute("UPDATE batches SET status=?, error=?, updated_at=? WHERE id=?",
                  (status, error, time.time(), batch_id))


def save_batch_result(batch_id, removal_ids, output_blob_path, report):
    now = time.time()
    with _lock, conn() as c:
        c.execute(
            "UPDATE batches SET status='done', removal_ids=?, output_blob_path=?, report_json=?, updated_at=? WHERE id=?",
            (json.dumps(removal_ids), output_blob_path, json.dumps(report), now, batch_id))


def get_batch(batch_id):
    with conn() as c:
        row = c.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        return dict(row) if row else None


def expired_batch_blobs(now=None):
    now = now or time.time()
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id, output_blob_path FROM batches WHERE output_blob_path IS NOT NULL AND output_blob_expires_at IS NOT NULL AND output_blob_expires_at < ?",
            (now,)).fetchall()]
