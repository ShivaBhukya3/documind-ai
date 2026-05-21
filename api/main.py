"""DocuMind AI — FastAPI application entry-point."""

import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

load_dotenv()

# Global pipeline instance (initialised at startup)
_pipeline = None


def get_pipeline():
    """Return the global RAGPipeline instance."""
    return _pipeline


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline
    logger.info("DocuMind AI API starting up ...")
    try:
        from src.database import init_db
        init_db()
        logger.info("Database initialised.")
    except Exception as exc:
        logger.error(f"Failed to initialise database: {exc}")

    try:
        from src.rag_pipeline import RAGPipeline
        _pipeline = RAGPipeline()
        logger.info("RAG Pipeline initialised successfully.")
    except Exception as exc:
        logger.error(f"Failed to initialise RAG pipeline: {exc}")
        _pipeline = None

    yield

    logger.info("DocuMind AI API shutting down ...")
    if _pipeline is not None:
        try:
            _pipeline.vector_store_manager.save_index()
            logger.info("Index saved on shutdown.")
        except Exception as exc:
            logger.warning(f"Could not save index on shutdown: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DocuMind AI",
    description=(
        "Intelligent Document Q&A System powered by RAG & LLMs. "
        "Upload documents and ask questions in natural language."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow_credentials must be False when allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms} ms)"
    )
    return response


# Simple in-memory rate limiter
_request_counts: dict[str, list[float]] = {}
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Per-IP rate limiting."""
    if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0

    timestamps = _request_counts.get(ip, [])
    timestamps = [t for t in timestamps if now - t < window]
    timestamps.append(now)
    _request_counts[ip] = timestamps

    if len(timestamps) > RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded. Max {RATE_LIMIT} requests per minute."},
        )
    return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# API key authentication (optional — only enforced when API_KEY is set)
# ─────────────────────────────────────────────────────────────────────────────

API_KEY = os.getenv("API_KEY", "")


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    """Enforce X-API-Key header when API_KEY env var is configured."""
    public_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
    if not API_KEY or request.url.path in public_paths or request.method == "OPTIONS":
        return await call_next(request)

    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key. Set X-API-Key header."},
        )
    return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# Global exception handler
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check logs for details."},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

from api.routes import chat, documents, health

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "DocuMind AI",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dev runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("APP_ENV", "production") == "development",
    )
