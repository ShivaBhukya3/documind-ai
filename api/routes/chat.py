"""Chat endpoints — Q&A, session reset, history, export."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from api.schemas.request_schemas import ChatRequest, ChatResetRequest
from api.schemas.response_schemas import (
    ChatResponse,
    ConversationHistoryResponse,
    MessageItem,
    ResetResponse,
    SourceDocument,
)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


def _get_pipeline():
    from api.main import get_pipeline
    pipeline = get_pipeline()
    if pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialised.")
    return pipeline


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, pipeline=Depends(_get_pipeline)):
    """Ask a question about the indexed documents.

    Set stream=true to receive a Server-Sent Events stream.
    """
    logger.info(f"Chat request | session={request.session_id} | question={request.question[:80]}...")

    if request.stream:
        async def event_stream():
            result = await asyncio.get_event_loop().run_in_executor(
                None, pipeline.query, request.question, request.session_id
            )
            answer = result.get("answer", "")
            words = answer.split()
            for i, word in enumerate(words):
                token = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.02)
            # Send final metadata event
            yield f"data: {json.dumps({'done': True, 'sources': result.get('sources', []), 'confidence': result.get('confidence_score', 0)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    result = pipeline.query(request.question, request.session_id)
    sources = [SourceDocument(**s) for s in result.get("sources", [])]
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=sources,
        confidence_score=result.get("confidence_score", 0.0),
        retrieval_time_ms=result.get("retrieval_time_ms", 0.0),
        generation_time_ms=result.get("generation_time_ms", 0.0),
        tokens_used=result.get("tokens_used", 0),
        session_id=result.get("session_id", request.session_id),
        relevant_chunks=result.get("relevant_chunks", 0),
    )


@router.post("/reset", response_model=ResetResponse)
async def reset_chat(request: ChatResetRequest, pipeline=Depends(_get_pipeline)):
    """Clear conversation history for a session."""
    pipeline.reset_conversation(request.session_id)
    return ResetResponse(
        success=True,
        message=f"Session '{request.session_id}' has been reset.",
    )


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_history(session_id: str, pipeline=Depends(_get_pipeline)):
    """Retrieve full conversation history for a session."""
    messages = pipeline.conversation_manager.get_history(session_id)
    stats = pipeline.conversation_manager.get_session_stats(session_id)
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[MessageItem(**m) for m in messages],
        session_stats=stats,
    )


@router.get("/export/{session_id}")
async def export_conversation(session_id: str, pipeline=Depends(_get_pipeline)):
    """Export conversation as a Markdown file download."""
    markdown = pipeline.export_conversation(session_id)
    return StreamingResponse(
        iter([markdown]),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="conversation_{session_id}.md"'
        },
    )
