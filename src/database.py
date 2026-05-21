"""SQLite database for persistent document metadata storage."""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = "data/documind.db"

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        with _lock:
            if _conn is None:
                Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
                _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                _conn.row_factory = sqlite3.Row
                _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def init_db() -> None:
    conn = _get_conn()
    with _lock:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                filename        TEXT    NOT NULL UNIQUE,
                file_type       TEXT    NOT NULL DEFAULT '',
                file_size_bytes INTEGER NOT NULL DEFAULT 0,
                chunks          INTEGER NOT NULL DEFAULT 0,
                vectors         INTEGER NOT NULL DEFAULT 0,
                status          TEXT    NOT NULL DEFAULT 'indexed',
                error           TEXT    NOT NULL DEFAULT '',
                s3_key          TEXT    NOT NULL DEFAULT '',
                s3_url          TEXT    NOT NULL DEFAULT '',
                uploaded_at     TEXT    NOT NULL
            )
        """)
        conn.commit()


def upsert_document(
    filename: str,
    file_type: str,
    file_size_bytes: int,
    chunks: int,
    vectors: int,
    status: str = "indexed",
    error: str = "",
    s3_key: str = "",
    s3_url: str = "",
) -> None:
    conn = _get_conn()
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _lock:
        conn.execute(
            """
            INSERT INTO documents
                (filename, file_type, file_size_bytes, chunks, vectors,
                 status, error, s3_key, s3_url, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                file_size_bytes = excluded.file_size_bytes,
                chunks          = excluded.chunks,
                vectors         = excluded.vectors,
                status          = excluded.status,
                error           = excluded.error,
                s3_key          = excluded.s3_key,
                s3_url          = excluded.s3_url,
                uploaded_at     = excluded.uploaded_at
            """,
            (filename, file_type, file_size_bytes, chunks, vectors,
             status, error, s3_key, s3_url, now),
        )
        conn.commit()


def list_documents() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY uploaded_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_document(filename: str) -> Optional[str]:
    """Delete metadata and return the s3_key so the caller can remove S3 object."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT s3_key FROM documents WHERE filename = ?", (filename,)
    ).fetchone()
    s3_key = row["s3_key"] if row else None
    with _lock:
        conn.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
    return s3_key


def get_document(filename: str) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM documents WHERE filename = ?", (filename,)
    ).fetchone()
    return dict(row) if row else None


def document_count() -> int:
    conn = _get_conn()
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
