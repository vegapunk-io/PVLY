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
CREATE TABLE IF NOT EXISTS sanitize_jobs (
  id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  status TEXT NOT NULL,            -- done | error
  filename TEXT,
  mime TEXT,
  format TEXT,
  bytes_in INTEGER,
  bytes_out INTEGER,
  sha256_in TEXT,
  sha256_out TEXT,
  policy_json TEXT,
  report_json TEXT,
  blob_path TEXT,
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_sanitize_created ON sanitize_jobs(created_at DESC);
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


def create_sanitize_job(job_id, filename, mime, fmt, bytes_in, sha256_in, policy: dict, blob_path):
    now = time.time()
    with _lock, conn() as c:
        c.execute(
            "INSERT INTO sanitize_jobs(id,created_at,status,filename,mime,format,bytes_in,sha256_in,policy_json,blob_path)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (job_id, now, "done", filename, mime, fmt, bytes_in, sha256_in, json.dumps(policy), blob_path))
        c.execute("INSERT INTO events(ts,scan_id,kind,detail) VALUES(?,?,?,?)", (now, job_id, "sanitize", filename))


def save_sanitize_report(job_id, report: dict, bytes_out, sha256_out):
    with _lock, conn() as c:
        c.execute("UPDATE sanitize_jobs SET status='done', report_json=?, bytes_out=?, sha256_out=? WHERE id=?",
                  (json.dumps(report), bytes_out, sha256_out, job_id))


def set_sanitize_error(job_id, error):
    with _lock, conn() as c:
        c.execute("UPDATE sanitize_jobs SET status='error', error=? WHERE id=?", (error[:500], job_id))


def get_sanitize_job(job_id):
    with conn() as c:
        row = c.execute("SELECT * FROM sanitize_jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def list_sanitize_jobs(limit=25):
    with conn() as c:
        rows = c.execute(
            "SELECT id,created_at,status,filename,format,bytes_in,bytes_out,sha256_in,sha256_out,report_json"
            " FROM sanitize_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            rep = json.loads(d.pop("report_json") or "{}")
            d["verdict"] = (rep.get("verify") or {}).get("verdict")
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
        return {"scans_total": total, "scans_done": done}
