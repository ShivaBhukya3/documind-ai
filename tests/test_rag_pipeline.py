"""Integration tests for RAGPipeline."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("FREE_MODE", "true")


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    """Create a fresh pipeline with a temp index for testing."""
    from src.rag_pipeline import RAGPipeline, load_config

    cfg = load_config("config/config.yaml")
    tmp = tmp_path_factory.mktemp("pipeline_test")
    cfg["vector_store"]["index_path"] = str(tmp / "idx")
    cfg["logging"]["file"] = str(tmp / "test.log")

    p = RAGPipeline.__new__(RAGPipeline)
    p.config_path = "config/config.yaml"
    p.config = cfg

    from src.conversation_manager import ConversationManager
    from src.document_processor import DocumentProcessor
    from src.embedding_engine import EmbeddingEngine
    from src.llm_chain import LLMChainManager
    from src.retriever import AdvancedRetriever
    from src.vector_store import VectorStoreManager

    p.document_processor = DocumentProcessor(cfg)
    p.embedding_engine = EmbeddingEngine(cfg)
    p.vector_store_manager = VectorStoreManager(cfg, p.embedding_engine.embeddings)
    p.llm_chain_manager = LLMChainManager(cfg)
    p.retriever = AdvancedRetriever(p.vector_store_manager, cfg)
    p.conversation_manager = ConversationManager(cfg)
    p._qa_chain = None
    p._ingested_docs = []
    return p


@pytest.fixture(scope="module")
def sample_txt(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("docs")
    f = tmp / "test_doc.txt"
    f.write_text(
        "TechCorp Leave Policy\n\n"
        "Employees receive 18 days of annual leave per year.\n"
        "Sick leave entitlement is 12 days annually.\n"
        "Maternity leave is 26 weeks under the Maternity Benefit Act 2017.\n"
        "Paternity leave is 10 days.\n"
        "Bereavement leave is 5 days for immediate family.\n"
        "Leave carry-forward: up to 10 days to next year.\n\n"
        "Financial Report FY2024\n\n"
        "Total revenue: ₹45 Crore, up 32% year-over-year.\n"
        "EBITDA margin: 28%. Net profit: ₹8.5 Crore.\n",
        encoding="utf-8",
    )
    return str(f)


class TestIngestDocuments:
    def test_ingest_txt_file(self, pipeline, sample_txt):
        report = pipeline.ingest_documents(sample_txt)
        assert report["chunks_created"] >= 1
        assert report["files_processed"] >= 1
        assert not report["errors"]

    def test_ingest_missing_file(self, pipeline):
        report = pipeline.ingest_documents("/nonexistent/file.pdf")
        assert report["files_processed"] == 0
        assert len(report["errors"]) >= 1

    def test_ingest_directory(self, pipeline, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("dir_test")
        (tmp / "a.txt").write_text("Leave policy: 18 annual days.")
        (tmp / "b.txt").write_text("Revenue: 45 crore in FY2024.")
        report = pipeline.ingest_documents(str(tmp))
        assert report["files_processed"] >= 2


class TestQuery:
    def test_query_returns_answer(self, pipeline, sample_txt):
        pipeline.ingest_documents(sample_txt)
        result = pipeline.query("How many annual leave days?")
        assert "answer" in result
        assert len(result["answer"]) > 0

    def test_query_returns_sources(self, pipeline):
        result = pipeline.query("What is the leave policy?")
        assert "sources" in result
        assert isinstance(result["sources"], list)

    def test_query_returns_confidence(self, pipeline):
        result = pipeline.query("maternity leave duration")
        assert "confidence_score" in result
        assert 0.0 <= result["confidence_score"] <= 1.0

    def test_query_with_session_id(self, pipeline):
        result = pipeline.query("what is annual leave?", session_id="test_session_001")
        assert result["session_id"] == "test_session_001"

    def test_query_no_documents(self, tmp_path):
        from src.rag_pipeline import RAGPipeline, load_config

        cfg = load_config("config/config.yaml")
        cfg["vector_store"]["index_path"] = str(tmp_path / "empty_idx")
        cfg["logging"]["file"] = str(tmp_path / "test.log")

        from src.conversation_manager import ConversationManager
        from src.document_processor import DocumentProcessor
        from src.embedding_engine import EmbeddingEngine
        from src.llm_chain import LLMChainManager
        from src.retriever import AdvancedRetriever
        from src.vector_store import VectorStoreManager

        p = RAGPipeline.__new__(RAGPipeline)
        p.config = cfg
        p.document_processor = DocumentProcessor(cfg)
        p.embedding_engine = EmbeddingEngine(cfg)
        p.vector_store_manager = VectorStoreManager(cfg, p.embedding_engine.embeddings)
        p.llm_chain_manager = LLMChainManager(cfg)
        p.retriever = AdvancedRetriever(p.vector_store_manager, cfg)
        p.conversation_manager = ConversationManager(cfg)
        p._qa_chain = None
        p._ingested_docs = []

        result = p.query("test question")
        assert "no documents" in result["answer"].lower() or result.get("error") == "no_documents"


class TestConversationMemory:
    def test_query_with_history(self, pipeline):
        session = "conv_test_001"
        pipeline.query("What is the annual leave policy?", session_id=session)
        result2 = pipeline.query("How many days can be carried forward?", session_id=session)
        history = pipeline.conversation_manager.get_history(session)
        assert len(history) >= 2

    def test_reset_conversation(self, pipeline):
        session = "reset_test_001"
        pipeline.query("test question", session_id=session)
        pipeline.reset_conversation(session)
        history = pipeline.conversation_manager.get_history(session)
        assert len(history) == 0


class TestHealthCheck:
    def test_health_check_returns_dict(self, pipeline, sample_txt):
        pipeline.ingest_documents(sample_txt)
        health = pipeline.health_check()
        assert "status" in health
        assert "components" in health
        assert "timestamp" in health

    def test_health_check_components_present(self, pipeline):
        health = pipeline.health_check()
        expected = ["embedding_engine", "vector_store", "llm", "document_processor"]
        for comp in expected:
            assert comp in health["components"]
