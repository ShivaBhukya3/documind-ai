"""RAG pipeline — main orchestrator wiring all components together."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from src.conversation_manager import ConversationManager
from src.document_processor import DocumentProcessor, load_config
from src.embedding_engine import EmbeddingEngine
from src.llm_chain import LLMChainManager
from src.retriever import AdvancedRetriever
from src.vector_store import VectorStoreManager


class RAGPipeline:
    """End-to-end RAG pipeline: ingest → embed → retrieve → generate.

    Acts as the single entry point for the dashboard and API layers.
    """

    def __init__(self, config_path: str = "config/config.yaml") -> None:
        """Initialise all pipeline components from a config file.

        Args:
            config_path: Path to config.yaml.
        """
        self.config_path = config_path
        self.config = load_config(config_path)

        # Setup loguru file sink
        log_file = self.config.get("logging", {}).get("file", "logs/app.log")
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            rotation=self.config.get("logging", {}).get("rotation", "10 MB"),
            retention=self.config.get("logging", {}).get("retention", "7 days"),
            level=self.config.get("logging", {}).get("level", "INFO"),
            format=self.config.get(
                "logging", {}).get(
                "format",
                "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
            ),
        )

        logger.info("Initialising DocuMind AI RAG Pipeline ...")

        self.document_processor = DocumentProcessor(self.config)
        self.embedding_engine = EmbeddingEngine(self.config)
        self.vector_store_manager = VectorStoreManager(
            self.config, self.embedding_engine.embeddings
        )
        self.llm_chain_manager = LLMChainManager(self.config)
        self.retriever = AdvancedRetriever(
            self.vector_store_manager,
            self.config,
            llm=self.llm_chain_manager.llm,
        )
        self.conversation_manager = ConversationManager(self.config)

        # QA chain (built lazily — needs documents to be ingested first)
        self._qa_chain = None
        self._ingested_docs: list[str] = []

        logger.info("RAG Pipeline ready.")

    # ─────────────────────────────────────────────────────────────────────────
    # Ingestion
    # ─────────────────────────────────────────────────────────────────────────

    def ingest_documents(self, source: str) -> dict:
        """Ingest documents from a file path, directory, or URL.

        Args:
            source: File path, directory path, or web URL.

        Returns:
            Ingestion report dict.
        """
        start = time.time()
        errors: list[str] = []
        raw_docs = []

        try:
            if source.startswith("http://") or source.startswith("https://"):
                logger.info(f"Ingesting URL: {source}")
                raw_docs = [self.document_processor.extract_url(source)]
            elif Path(source).is_dir():
                logger.info(f"Ingesting directory: {source}")
                raw_docs = self.document_processor.load_multiple_documents(source)
            elif Path(source).is_file():
                logger.info(f"Ingesting file: {source}")
                raw_docs = self.document_processor.load_document(source)
            else:
                raise ValueError(f"Source not found: {source}")
        except Exception as exc:
            errors.append(str(exc))
            logger.error(f"Ingestion failed: {exc}")

        if not raw_docs:
            return {
                "files_processed": 0,
                "chunks_created": 0,
                "vectors_stored": 0,
                "time_taken_s": round(time.time() - start, 2),
                "errors": errors,
            }

        chunks = self.document_processor.chunk_documents(raw_docs)
        chunks = self.document_processor.deduplicate_documents(chunks)

        self.vector_store_manager.add_documents(chunks)
        self._rebuild_qa_chain()

        # Track ingested files
        new_files = list({
            c.metadata.get("filename", source) for c in chunks
        })
        self._ingested_docs.extend(new_files)

        elapsed = round(time.time() - start, 2)
        report = {
            "files_processed": len(new_files),
            "chunks_created": len(chunks),
            "vectors_stored": self.vector_store_manager.get_index_stats().get("total_vectors", 0),
            "time_taken_s": elapsed,
            "errors": errors,
            "files": new_files,
        }
        logger.info(f"Ingestion complete: {report}")
        return report

    # ─────────────────────────────────────────────────────────────────────────
    # Query
    # ─────────────────────────────────────────────────────────────────────────

    def query(self, question: str, session_id: str = "default") -> dict:
        """Execute a full RAG query and return a structured response.

        Args:
            question: User's natural-language question.
            session_id: Session identifier for conversation memory.

        Returns:
            Dict with answer, sources, confidence, timings, and metadata.
        """
        if self.vector_store_manager.vector_store is None:
            return {
                "answer": "No documents have been ingested yet. Please upload documents first.",
                "sources": [],
                "confidence_score": 0.0,
                "session_id": session_id,
                "error": "no_documents",
            }

        retrieval_start = time.time()
        docs = self.retriever.get_relevant_documents(question)
        retrieval_time = round((time.time() - retrieval_start) * 1000, 1)

        if not docs:
            return {
                "answer": "I could not find relevant information in the indexed documents.",
                "sources": [],
                "confidence_score": 0.0,
                "retrieval_time_ms": retrieval_time,
                "generation_time_ms": 0,
                "tokens_used": 0,
                "session_id": session_id,
                "relevant_chunks": 0,
            }

        memory = self.conversation_manager.get_memory_object(session_id)

        if self._qa_chain is None:
            self._rebuild_qa_chain()

        generation_start = time.time()
        try:
            result = self._qa_chain.invoke({"question": question})
            answer = result.get("answer", "I could not generate an answer.")
            source_docs = result.get("source_documents", docs)
        except Exception as exc:
            logger.error(f"Chain invocation failed: {exc}")
            # Fallback: format context manually and call LLM directly
            context = self.retriever.format_docs_for_context(docs)
            answer = self._fallback_answer(question, context)
            source_docs = docs

        generation_time = round((time.time() - generation_start) * 1000, 1)

        sources = _extract_sources(source_docs)
        confidence = _estimate_confidence(answer, source_docs)

        # Update conversation memory
        self.conversation_manager.add_message(session_id, "human", question)
        self.conversation_manager.add_message(session_id, "ai", answer)
        for src in sources:
            self.conversation_manager.add_source_to_session(session_id, src.get("filename", ""))

        # Estimate token usage
        tokens_approx = len(question.split()) + len(answer.split())

        return {
            "answer": answer,
            "sources": sources,
            "confidence_score": confidence,
            "retrieval_time_ms": retrieval_time,
            "generation_time_ms": generation_time,
            "tokens_used": tokens_approx,
            "session_id": session_id,
            "relevant_chunks": len(source_docs),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Document summarisation
    # ─────────────────────────────────────────────────────────────────────────

    def get_document_summary(self, doc_name: str) -> str:
        """Generate a bullet-point summary of a specific document.

        Args:
            doc_name: Filename of the document to summarise.

        Returns:
            Markdown-formatted summary string.
        """
        if self.vector_store_manager.vector_store is None:
            return "No documents indexed."

        # Retrieve representative chunks for this document
        docs = self.retriever.get_relevant_documents(f"summary of {doc_name}")
        relevant = [d for d in docs if doc_name in d.metadata.get("source", "")][:5]
        if not relevant:
            relevant = docs[:3]

        if not relevant:
            return f"Could not find content for: {doc_name}"

        text = "\n\n".join(d.page_content for d in relevant)
        chain = self.llm_chain_manager.build_summary_chain()
        try:
            result = chain.invoke({"document_text": text[:4000]})
            return result.get("text", result) if isinstance(result, dict) else str(result)
        except Exception as exc:
            logger.error(f"Summary generation failed: {exc}")
            return f"Error generating summary: {exc}"

    # ─────────────────────────────────────────────────────────────────────────
    # Session management
    # ─────────────────────────────────────────────────────────────────────────

    def reset_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self.conversation_manager.clear_session(session_id)
        logger.info(f"Conversation reset for session: {session_id}")

    def export_conversation(self, session_id: str) -> str:
        """Export a conversation as a Markdown-formatted string."""
        session_data = self.conversation_manager.export_session(session_id)
        if "error" in session_data:
            return session_data["error"]

        lines = [
            f"# DocuMind AI — Conversation Export",
            f"**Session ID:** {session_id}",
            f"**Created:** {session_data.get('created_at', 'N/A')}",
            f"**Messages:** {session_data.get('message_count', 0)}",
            "",
            "---",
            "",
        ]
        for msg in session_data.get("messages", []):
            role = "**You**" if msg["role"] == "human" else "**DocuMind AI**"
            lines.append(f"{role}: {msg['content']}\n")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Health & stats
    # ─────────────────────────────────────────────────────────────────────────

    def health_check(self) -> dict:
        """Check health of all pipeline components."""
        vs_stats = self.vector_store_manager.get_index_stats()
        emb_ok = self.embedding_engine.test_embeddings()

        return {
            "status": "healthy" if emb_ok else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "embedding_engine": "ok" if emb_ok else "error",
                "vector_store": "ok" if vs_stats.get("is_loaded") else "empty",
                "llm": "configured",
                "document_processor": "ok",
                "conversation_manager": "ok",
            },
            "index_stats": vs_stats,
            "embedding_stats": self.embedding_engine.get_embedding_stats(),
        }

    def get_pipeline_stats(self) -> dict:
        """Return combined statistics from all components."""
        return {
            "vector_store": self.vector_store_manager.get_index_stats(),
            "embeddings": self.embedding_engine.get_embedding_stats(),
            "llm": self.llm_chain_manager.get_llm_stats(),
            "ingested_docs": self._ingested_docs,
            "active_sessions": len(self.conversation_manager.list_sessions()),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _rebuild_qa_chain(self) -> None:
        retriever = self.vector_store_manager.get_retriever()
        default_memory = self.conversation_manager.get_memory_object("default")
        self._qa_chain = self.llm_chain_manager.build_qa_chain(retriever, default_memory)

    def _fallback_answer(self, question: str, context: str) -> str:
        """Direct LLM call when chain invocation fails."""
        try:
            prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
            return self.llm_chain_manager.llm.predict(prompt)
        except Exception:
            return "I'm unable to answer at this time. Please check that your LLM is configured correctly."


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_sources(docs) -> list[dict]:
    sources = []
    seen: set[str] = set()
    for doc in docs:
        meta = doc.metadata
        key = meta.get("source", "") + str(meta.get("page", ""))
        if key not in seen:
            seen.add(key)
            sources.append({
                "filename": meta.get("filename", meta.get("source", "Unknown")),
                "page": meta.get("page", meta.get("slide", meta.get("section", "N/A"))),
                "file_type": meta.get("file_type", "unknown"),
                "chunk_id": meta.get("chunk_id", ""),
                "preview": doc.page_content[:200] + "...",
            })
    return sources


def _estimate_confidence(answer: str, docs) -> float:
    """Heuristic confidence score: longer answer + more sources → higher confidence."""
    if not answer or not docs:
        return 0.0
    answer_score = min(len(answer.split()) / 50, 1.0) * 0.5
    source_score = min(len(docs) / 5, 1.0) * 0.5
    penalty = 0.2 if "don't have" in answer.lower() or "cannot find" in answer.lower() else 0.0
    return round(max(0.0, answer_score + source_score - penalty), 2)


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry-point for quick testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pipeline = RAGPipeline()
    report = pipeline.ingest_documents("data/raw/sample_docs")
    print(f"\nIngestion: {json.dumps(report, indent=2)}")
    result = pipeline.query("What is the leave policy at TechCorp?")
    print(f"\nAnswer: {result['answer']}")
    print(f"Sources: {[s['filename'] for s in result['sources']]}")
    print(f"Confidence: {result['confidence_score']}")
