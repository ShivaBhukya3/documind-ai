"""Pydantic request schemas for the DocuMind AI API."""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to ask about the indexed documents.",
        examples=["What is the leave policy at TechCorp?"],
    )
    session_id: str = Field(
        default="default",
        max_length=100,
        description="Session identifier for conversation memory.",
    )
    stream: bool = Field(
        default=False,
        description="Enable server-sent events streaming for the response.",
    )


class ChatResetRequest(BaseModel):
    session_id: str = Field(
        ...,
        description="The session ID to reset.",
        examples=["user_abc123"],
    )


class DocumentURLRequest(BaseModel):
    url: str = Field(
        ...,
        description="A publicly accessible URL to index.",
        examples=["https://en.wikipedia.org/wiki/Retrieval-augmented_generation"],
    )


class DeleteDocumentRequest(BaseModel):
    doc_id: str = Field(
        ...,
        description="Filename or document identifier to remove from the index.",
    )
