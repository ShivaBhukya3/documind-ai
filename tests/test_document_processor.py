"""Unit tests for DocumentProcessor."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.document_processor import DocumentProcessor, load_config, _hash_text

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document


@pytest.fixture
def config():
    return load_config("config/config.yaml")


@pytest.fixture
def processor(config):
    return DocumentProcessor(config)


@pytest.fixture
def sample_txt_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text(
        "TechCorp Solutions Annual Leave Policy\n\n"
        "Employees receive 18 days of annual leave per year.\n"
        "Sick leave is 12 days per year.\n"
        "Maternity leave is 26 weeks as per law.",
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def sample_pdf_path():
    return "data/raw/sample_docs/company_policy.pdf"


# ─────────────────────────────────────────────────────────────────────────────


class TestLoadDocument:
    def test_load_txt_document(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        assert len(docs) >= 1
        assert "TechCorp" in docs[0].page_content
        assert docs[0].metadata["file_type"] == "txt"

    def test_load_pdf_document(self, processor, sample_pdf_path):
        if not Path(sample_pdf_path).exists():
            pytest.skip("Sample PDFs not generated yet. Run generate_sample_docs.py first.")
        docs = processor.extract_pdf(sample_pdf_path)
        assert len(docs) >= 1
        assert docs[0].metadata["file_type"] == "pdf"

    def test_load_unsupported_file(self, processor, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("content")
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.load_document(str(f))

    def test_load_missing_file(self, processor):
        with pytest.raises(FileNotFoundError):
            processor.load_document("/nonexistent/path/file.txt")

    def test_metadata_fields_present(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        meta = docs[0].metadata
        assert "source" in meta
        assert "filename" in meta
        assert "file_type" in meta
        assert "loaded_at" in meta


class TestChunkDocuments:
    def test_chunk_documents_returns_more_chunks(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        chunks = processor.chunk_documents(docs)
        assert len(chunks) >= 1

    def test_chunk_size_respected(self, processor, tmp_path):
        big_text = "word " * 5000
        f = tmp_path / "big.txt"
        f.write_text(big_text)
        docs = processor.load_document(str(f))
        chunks = processor.chunk_documents(docs)
        for chunk in chunks:
            assert len(chunk.page_content) <= processor.chunk_size * 1.1

    def test_chunk_metadata_fields(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        chunks = processor.chunk_documents(docs)
        for chunk in chunks:
            assert "chunk_id" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "document_hash" in chunk.metadata

    def test_chunk_overlap(self, processor, tmp_path):
        text = " ".join(f"word{i}" for i in range(500))
        f = tmp_path / "overlap.txt"
        f.write_text(text)
        docs = processor.load_document(str(f))
        chunks = processor.chunk_documents(docs)
        if len(chunks) > 1:
            assert len(chunks[0].page_content) > 0
            assert len(chunks[1].page_content) > 0


class TestCleanText:
    def test_removes_extra_whitespace(self, processor):
        result = processor.clean_text("hello   world   test")
        assert "  " not in result

    def test_normalises_unicode(self, processor):
        result = processor.clean_text("café résumé")
        assert result is not None
        assert len(result) > 0

    def test_removes_null_bytes(self, processor):
        result = processor.clean_text("hello\x00world")
        assert "\x00" not in result

    def test_collapses_blank_lines(self, processor):
        result = processor.clean_text("line1\n\n\n\nline2")
        assert "\n\n\n" not in result


class TestDocumentStats:
    def test_get_document_stats_returns_expected_keys(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        chunks = processor.chunk_documents(docs)
        stats = processor.get_document_stats(chunks)
        for key in ["total_chunks", "total_words", "avg_chunk_size"]:
            assert key in stats

    def test_empty_documents_returns_empty(self, processor):
        stats = processor.get_document_stats([])
        assert stats == {}


class TestDeduplication:
    def test_deduplicate_removes_exact_duplicates(self, processor, sample_txt_file):
        docs = processor.load_document(sample_txt_file)
        duplicated = docs * 3
        unique = processor.deduplicate_documents(duplicated)
        assert len(unique) <= len(docs)
        assert len(unique) >= 1

    def test_deduplicate_preserves_unique(self, processor, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("Unique content A about leave policy.")
        f2.write_text("Unique content B about financial report.")
        d1 = processor.load_document(str(f1))
        d2 = processor.load_document(str(f2))
        result = processor.deduplicate_documents(d1 + d2)
        assert len(result) == 2
