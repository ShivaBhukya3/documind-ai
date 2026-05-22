"""Document metadata storage — SQLite (local) or PostgreSQL (production via DATABASE_URL)."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from loguru import logger

# ── Engine ────────────────────────────────────────────────────────────────────

_raw_url = os.getenv("DATABASE_URL", "").strip("\"'")
# Strip Prisma-only params SQLAlchemy can't parse
_raw_url = _raw_url.split("?pgbouncer=")[0].split("&pgbouncer=")[0]
if _raw_url:
    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)
    _DB_URL = _raw_url
    _CONNECT_ARGS: dict = {}
else:
    _db_path = "data/documind.db"
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    _DB_URL = f"sqlite:///{_db_path}"
    _CONNECT_ARGS = {"check_same_thread": False}

engine = create_engine(_DB_URL, connect_args=_CONNECT_ARGS, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ── Model ─────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "documents"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    filename        = Column(String, nullable=False, unique=True)
    file_type       = Column(String, default="")
    file_size_bytes = Column(Integer, default=0)
    chunks          = Column(Integer, default=0)
    vectors         = Column(Integer, default=0)
    status          = Column(String, default="indexed")
    error           = Column(String, default="")
    s3_key          = Column(String, default="")
    s3_url          = Column(String, default="")
    uploaded_at     = Column(String, nullable=False, default="")


# ── Public API ────────────────────────────────────────────────────────────────

def init_db() -> None:
    Base.metadata.create_all(engine)
    logger.info(f"Database ready ({_DB_URL[:30]}...).")


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
    now = datetime.utcnow().isoformat(timespec="seconds")
    with SessionLocal() as session:
        doc = session.query(DocumentRecord).filter_by(filename=filename).first()
        if doc:
            doc.file_type       = file_type
            doc.file_size_bytes = file_size_bytes
            doc.chunks          = chunks
            doc.vectors         = vectors
            doc.status          = status
            doc.error           = error
            doc.s3_key          = s3_key
            doc.s3_url          = s3_url
            doc.uploaded_at     = now
        else:
            session.add(DocumentRecord(
                filename=filename, file_type=file_type,
                file_size_bytes=file_size_bytes, chunks=chunks,
                vectors=vectors, status=status, error=error,
                s3_key=s3_key, s3_url=s3_url, uploaded_at=now,
            ))
        session.commit()


def list_documents() -> list[dict]:
    with SessionLocal() as session:
        rows = session.query(DocumentRecord).order_by(DocumentRecord.uploaded_at.desc()).all()
        return [_to_dict(r) for r in rows]


def delete_document(filename: str) -> Optional[str]:
    with SessionLocal() as session:
        doc = session.query(DocumentRecord).filter_by(filename=filename).first()
        s3_key = doc.s3_key if doc else None
        if doc:
            session.delete(doc)
            session.commit()
        return s3_key


def get_document(filename: str) -> Optional[dict]:
    with SessionLocal() as session:
        doc = session.query(DocumentRecord).filter_by(filename=filename).first()
        return _to_dict(doc) if doc else None


def document_count() -> int:
    with SessionLocal() as session:
        return session.query(DocumentRecord).count()


def _to_dict(doc: DocumentRecord) -> dict:
    return {
        "id":              doc.id,
        "filename":        doc.filename,
        "file_type":       doc.file_type,
        "file_size_bytes": doc.file_size_bytes,
        "chunks":          doc.chunks,
        "vectors":         doc.vectors,
        "status":          doc.status,
        "error":           doc.error,
        "s3_key":          doc.s3_key,
        "s3_url":          doc.s3_url,
        "uploaded_at":     doc.uploaded_at,
    }
