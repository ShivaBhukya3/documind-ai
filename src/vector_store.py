"""Vector store manager — FAISS-backed document index with persistence."""

import json
import os
import pickle
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


class VectorStoreManager:
    """Manage a FAISS vector index: create, load, update, search, persist.

    All FAISS indexes are saved to disk so they survive across restarts.
    """

    def __init__(self, config: dict, embeddings) -> None:
        """Initialise with app config and a LangChain Embeddings object.

        Args:
            config: Full application config dict.
            embeddings: LangChain-compatible Embeddings instance.
        """
        self.config = config
        self.embeddings = embeddings
        vs_cfg = config.get("vector_store", {})
        self.index_path: str = vs_cfg.get("index_path", "data/processed/embeddings/faiss_index")
        self.top_k: int = vs_cfg.get("top_k", 5)
        self.score_threshold: float = config.get("retrieval", {}).get("score_threshold", 0.3)

        self.vector_store: Optional[FAISS] = None
        self._doc_metadata: dict[str, dict] = {}  # doc_hash → metadata
        self._created_at: Optional[str] = None
        self._last_updated: Optional[str] = None

        # Restore from Supabase Storage if local index is missing
        local_index = Path(self.index_path) / "index.faiss"
        if not local_index.exists():
            self._supabase_download()

        # Auto-load existing index if present
        if (Path(self.index_path) / "index.faiss").exists():
            self._try_load_index()

    # ─────────────────────────────────────────────────────────────────────────
    # Index lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def create_vector_store(self, documents: list[Document]) -> FAISS:
        """Build a new FAISS index from scratch.

        Args:
            documents: Chunked Document objects to index.

        Returns:
            The created FAISS vector store.
        """
        if not documents:
            raise ValueError("Cannot create vector store from empty document list.")

        logger.info(f"Creating FAISS index from {len(documents)} chunks ...")
        start = time.time()

        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self._last_updated = _now_iso()
        self._created_at = self._created_at or self._last_updated

        elapsed = time.time() - start
        logger.info(
            f"FAISS index created: {len(documents)} vectors in {elapsed:.2f}s."
        )
        self.save_index()
        return self.vector_store

    def load_vector_store(self, index_path: Optional[str] = None) -> FAISS:
        """Load an existing FAISS index from disk.

        Args:
            index_path: Directory containing index.faiss and index.pkl.
                        Defaults to path from config.

        Returns:
            Loaded FAISS vector store.
        """
        path = index_path or self.index_path
        faiss_file = Path(path) / "index.faiss"
        if not faiss_file.exists():
            raise FileNotFoundError(f"No FAISS index found at: {path}")

        logger.info(f"Loading FAISS index from {path} ...")
        self.vector_store = FAISS.load_local(
            path, self.embeddings, allow_dangerous_deserialization=True
        )
        self._load_meta(path)
        logger.info("FAISS index loaded successfully.")
        return self.vector_store

    def add_documents(self, documents: list[Document]) -> None:
        """Add documents to an existing index (or create one).

        Args:
            documents: New chunked Document objects to add.
        """
        if not documents:
            return

        if self.vector_store is None:
            self.create_vector_store(documents)
            return

        # Dedup by document_hash metadata field
        existing_hashes = {
            meta.get("document_hash")
            for meta in self._doc_metadata.values()
        }
        new_docs = [
            d for d in documents
            if d.metadata.get("document_hash") not in existing_hashes
        ]

        if not new_docs:
            logger.info("No new documents to add (all already indexed).")
            return

        logger.info(f"Adding {len(new_docs)} new chunks to FAISS index.")
        self.vector_store.add_documents(new_docs)
        self._last_updated = _now_iso()
        self.save_index()

    def delete_documents(self, doc_ids: list[str]) -> None:
        """Remove documents by source filename and rebuild the index.

        Args:
            doc_ids: List of source filenames (e.g. 'company_policy.pdf').
        """
        if self.vector_store is None:
            return

        logger.warning(
            "FAISS does not support deletion natively — rebuilding index without target docs."
        )
        all_docs = _get_all_docs_from_store(self.vector_store)
        filtered = [
            d for d in all_docs
            if d.metadata.get("filename") not in doc_ids
        ]
        logger.info(f"Rebuilding index with {len(filtered)} chunks (removed from: {doc_ids}).")
        self.create_vector_store(filtered)

    def clear_index(self) -> None:
        """Delete all vectors and reset the index."""
        self.vector_store = None
        self._doc_metadata = {}
        import shutil
        idx_path = Path(self.index_path)
        if idx_path.exists():
            shutil.rmtree(idx_path)
            idx_path.mkdir(parents=True, exist_ok=True)
        logger.info("FAISS index cleared.")

    # ─────────────────────────────────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────────────────────────────────

    def similarity_search(self, query: str, k: Optional[int] = None) -> list[Document]:
        """Standard cosine-similarity search.

        Args:
            query: Natural-language query string.
            k: Number of results to return. Defaults to config top_k.

        Returns:
            Top-k most similar document chunks.
        """
        self._assert_loaded()
        k = k or self.top_k
        return self.vector_store.similarity_search(query, k=k)

    def mmr_search(
        self,
        query: str,
        k: Optional[int] = None,
        fetch_k: Optional[int] = None,
    ) -> list[Document]:
        """Maximal Marginal Relevance search — balances relevance and diversity.

        Args:
            query: Natural-language query string.
            k: Number of results to return.
            fetch_k: Candidate pool size before MMR filtering.

        Returns:
            Diverse top-k document chunks.
        """
        self._assert_loaded()
        retrieval_cfg = self.config.get("retrieval", {})
        k = k or self.top_k
        fetch_k = fetch_k or retrieval_cfg.get("fetch_k", 20)
        lambda_mult = retrieval_cfg.get("lambda_mult", 0.5)
        return self.vector_store.max_marginal_relevance_search(
            query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
        )

    def similarity_search_with_score(self, query: str) -> list[tuple[Document, float]]:
        """Search and return (document, score) tuples filtered by threshold.

        Args:
            query: Natural-language query string.

        Returns:
            List of (Document, similarity_score) tuples above threshold.
        """
        self._assert_loaded()
        results = self.vector_store.similarity_search_with_score(query, k=self.top_k * 2)
        # FAISS returns L2 distance; lower = more similar. Convert to similarity.
        filtered = [
            (doc, float(score))
            for doc, score in results
            if float(score) <= (1 - self.score_threshold)  # L2 distance threshold
        ]
        return filtered[: self.top_k]

    def get_retriever(self, search_type: Optional[str] = None):
        """Return a LangChain VectorStoreRetriever.

        Args:
            search_type: 'similarity', 'mmr', or None (uses config default).

        Returns:
            Configured VectorStoreRetriever.
        """
        self._assert_loaded()
        search_type = search_type or self.config.get("retrieval", {}).get("search_type", "mmr")
        retrieval_cfg = self.config.get("retrieval", {})

        if search_type == "mmr":
            return self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": self.top_k,
                    "fetch_k": retrieval_cfg.get("fetch_k", 20),
                    "lambda_mult": retrieval_cfg.get("lambda_mult", 0.5),
                },
            )
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Persistence & stats
    # ─────────────────────────────────────────────────────────────────────────

    def save_index(self) -> None:
        """Persist FAISS index to disk and back up to Supabase Storage."""
        if self.vector_store is None:
            return
        path = Path(self.index_path)
        path.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(str(path))
        self._save_meta(str(path))
        logger.info(f"FAISS index saved to {path}.")
        self._supabase_upload()

    def get_index_stats(self) -> dict:
        """Return statistics about the current index."""
        path = Path(self.index_path)
        size_mb = 0.0
        faiss_file = path / "index.faiss"
        if faiss_file.exists():
            size_mb = faiss_file.stat().st_size / (1024 * 1024)

        total_vectors = 0
        if self.vector_store is not None:
            try:
                total_vectors = self.vector_store.index.ntotal
            except Exception:
                pass

        return {
            "total_vectors": total_vectors,
            "index_size_mb": round(size_mb, 3),
            "index_path": str(path),
            "embedding_model": self.config.get("embeddings", {}).get("model_name", "unknown"),
            "last_updated": self._last_updated,
            "created_at": self._created_at,
            "is_loaded": self.vector_store is not None,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _assert_loaded(self) -> None:
        if self.vector_store is None:
            raise RuntimeError(
                "Vector store not initialised. Call create_vector_store() or load_vector_store() first."
            )

    def _try_load_index(self) -> None:
        try:
            self.load_vector_store()
        except Exception as exc:
            logger.warning(f"Could not auto-load existing index: {exc}")

    def _save_meta(self, path: str) -> None:
        meta = {
            "created_at": self._created_at,
            "last_updated": self._last_updated,
        }
        with open(os.path.join(path, "meta.json"), "w") as f:
            json.dump(meta, f)

    def _load_meta(self, path: str) -> None:
        meta_file = os.path.join(path, "meta.json")
        if os.path.exists(meta_file):
            with open(meta_file) as f:
                meta = json.load(f)
            self._created_at = meta.get("created_at")
            self._last_updated = meta.get("last_updated")

    def _supabase_upload(self) -> None:
        """Upload FAISS index files to Supabase Storage (no-op if env vars not set)."""
        s_url = os.getenv("SUPABASE_URL", "").strip()
        s_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        if not s_url or not s_key:
            return
        try:
            import requests as _req
            hdrs = {"Authorization": f"Bearer {s_key}", "apikey": s_key}
            bucket = "faiss-index"
            _req.post(f"{s_url}/storage/v1/bucket", json={"name": bucket, "public": False}, headers=hdrs)
            path = Path(self.index_path)
            for fname in ["index.faiss", "index.pkl", "meta.json"]:
                fpath = path / fname
                if not fpath.exists():
                    continue
                data = fpath.read_bytes()
                resp = _req.post(
                    f"{s_url}/storage/v1/object/{bucket}/{fname}",
                    headers={**hdrs, "x-upsert": "true", "Content-Type": "application/octet-stream"},
                    data=data,
                )
                if resp.status_code in (200, 201):
                    logger.debug(f"Uploaded {fname} to Supabase Storage.")
                else:
                    logger.warning(f"Supabase upload {fname} failed: {resp.text[:200]}")
        except Exception as exc:
            logger.warning(f"Supabase upload skipped: {exc}")

    def _supabase_download(self) -> None:
        """Download FAISS index files from Supabase Storage (no-op if env vars not set)."""
        s_url = os.getenv("SUPABASE_URL", "").strip()
        s_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
        if not s_url or not s_key:
            return
        try:
            import requests as _req
            hdrs = {"Authorization": f"Bearer {s_key}", "apikey": s_key}
            bucket = "faiss-index"
            check = _req.get(f"{s_url}/storage/v1/object/{bucket}/index.faiss", headers=hdrs)
            if check.status_code != 200:
                logger.info("No FAISS backup found in Supabase Storage.")
                return
            path = Path(self.index_path)
            path.mkdir(parents=True, exist_ok=True)
            for fname in ["index.faiss", "index.pkl", "meta.json"]:
                resp = _req.get(f"{s_url}/storage/v1/object/{bucket}/{fname}", headers=hdrs)
                if resp.status_code == 200:
                    (path / fname).write_bytes(resp.content)
                    logger.debug(f"Downloaded {fname} from Supabase Storage.")
            logger.info("FAISS index restored from Supabase Storage.")
        except Exception as exc:
            logger.warning(f"Supabase download skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()


def _get_all_docs_from_store(store: FAISS) -> list[Document]:
    """Extract all documents stored in a FAISS docstore."""
    try:
        return list(store.docstore._dict.values())
    except Exception:
        return []
