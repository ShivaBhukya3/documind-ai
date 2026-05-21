"""Pydantic response schemas for the DocuMind AI API."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    filename: str
    page: Any = None
    file_type: str = ""
    chunk_id: str = ""
    preview: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument] = Field(default_factory=list)
    confidence_score: float = 0.0
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    tokens_used: int = 0
    session_id: str = "default"
    relevant_chunks: int = 0


class DocumentInfo(BaseModel):
    filename: str
    file_type: str = ""
    file_size_bytes: int = 0
    chunks: int = 0
    status: str = "indexed"
    uploaded_at: str = ""
    error: str = ""
    s3_url: str = ""


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo] = Field(default_factory=list)
    total: int = 0


class IngestionResponse(BaseModel):
    doc_id: str = ""
    files_processed: int = 0
    chunks_created: int = 0
    vectors_stored: int = 0
    processing_time_s: float = 0.0
    status: str = "success"
    errors: list[str] = Field(default_factory=list)


class IndexStatsResponse(BaseModel):
    total_vectors: int = 0
    index_size_mb: float = 0.0
    index_path: str = ""
    embedding_model: str = ""
    last_updated: Optional[str] = None
    is_loaded: bool = False


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: dict[str, str] = Field(default_factory=dict)
    index_stats: dict = Field(default_factory=dict)


class MessageItem(BaseModel):
    role: str
    content: str


class ConversationHistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageItem] = Field(default_factory=list)
    session_stats: dict = Field(default_factory=dict)


class ResetResponse(BaseModel):
    success: bool
    message: str
