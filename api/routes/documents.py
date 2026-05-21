"""Document management endpoints — upload, list, delete, stats, URL ingestion."""

import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger

from api.schemas.request_schemas import DocumentURLRequest
from api.schemas.response_schemas import (
    DocumentInfo,
    DocumentListResponse,
    IndexStatsResponse,
    IngestionResponse,
)
from src.database import delete_document as db_delete, list_documents, upsert_document
from src.storage import delete_object as s3_delete, upload_bytes as s3_upload

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".pptx", ".md"}
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

CONTENT_TYPES = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt":  "text/plain",
    ".csv":  "text/csv",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".md":   "text/markdown",
}


def _get_pipeline():
    from api.main import get_pipeline
    pipeline = get_pipeline()
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialised.")
    return pipeline


@router.post("/upload", response_model=IngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    pipeline=Depends(_get_pipeline),
):
    """Upload and index a document (PDF, DOCX, TXT, CSV, PPTX, MD)."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_MB} MB.",
        )

    # Use the original filename so chunk metadata stores the real name, not a temp name
    safe_name = re.sub(r'[^\w\-_\. ]', '_', file.filename)
    tmp_dir = tempfile.mkdtemp(prefix="documind_")
    tmp_path = os.path.join(tmp_dir, safe_name)

    try:
        with open(tmp_path, "wb") as f:
            f.write(content)
        logger.info(f"Processing uploaded file: {file.filename}")
        report = pipeline.ingest_documents(tmp_path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    chunks = report.get("chunks_created", 0)
    vectors = report.get("vectors_stored", 0)
    errors = report.get("errors", [])
    status = "success" if not errors else "partial"

    s3_key = f"documents/{uuid.uuid4().hex}{ext}"
    s3_url = s3_upload(content, s3_key, CONTENT_TYPES.get(ext, "application/octet-stream")) or ""

    upsert_document(
        filename=file.filename,
        file_type=ext.lstrip("."),
        file_size_bytes=len(content),
        chunks=chunks,
        vectors=vectors,
        status=status,
        error="; ".join(errors) if errors else "",
        s3_key=s3_key if s3_url else "",
        s3_url=s3_url,
    )

    return IngestionResponse(
        doc_id=file.filename,
        files_processed=report.get("files_processed", 0),
        chunks_created=chunks,
        vectors_stored=vectors,
        processing_time_s=report.get("time_taken_s", 0.0),
        status=status,
        errors=errors,
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents_endpoint():
    """List all indexed documents from the database."""
    rows = list_documents()
    docs = [
        DocumentInfo(
            filename=r["filename"],
            file_type=r["file_type"],
            file_size_bytes=r["file_size_bytes"],
            chunks=r["chunks"],
            status=r["status"],
            uploaded_at=r["uploaded_at"],
            error=r.get("error", ""),
            s3_url=r.get("s3_url", ""),
        )
        for r in rows
    ]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{doc_id}")
async def delete_document_endpoint(doc_id: str, pipeline=Depends(_get_pipeline)):
    """Remove a document from the vector index, S3, and database."""
    logger.info(f"Deleting document: {doc_id}")
    try:
        pipeline.vector_store_manager.delete_documents([doc_id])
        if doc_id in pipeline._ingested_docs:
            pipeline._ingested_docs.remove(doc_id)
        s3_key = db_delete(doc_id)
        if s3_key:
            s3_delete(s3_key)
        return {"success": True, "message": f"Document '{doc_id}' removed."}
    except Exception as exc:
        logger.error(f"Delete failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats", response_model=IndexStatsResponse)
async def document_stats(pipeline=Depends(_get_pipeline)):
    """Return complete vector index statistics."""
    stats = pipeline.vector_store_manager.get_index_stats()
    return IndexStatsResponse(**stats)


@router.post("/url", response_model=IngestionResponse)
async def ingest_url(request: DocumentURLRequest, pipeline=Depends(_get_pipeline)):
    """Ingest and index content from a web URL."""
    logger.info(f"Ingesting URL: {request.url}")
    report = pipeline.ingest_documents(request.url)
    errors = report.get("errors", [])
    status = "success" if not errors else "error"

    upsert_document(
        filename=request.url,
        file_type="url",
        file_size_bytes=0,
        chunks=report.get("chunks_created", 0),
        vectors=report.get("vectors_stored", 0),
        status=status,
        error="; ".join(errors) if errors else "",
    )

    return IngestionResponse(
        doc_id=request.url,
        files_processed=report.get("files_processed", 0),
        chunks_created=report.get("chunks_created", 0),
        vectors_stored=report.get("vectors_stored", 0),
        processing_time_s=report.get("time_taken_s", 0.0),
        status=status,
        errors=errors,
    )
