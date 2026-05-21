"""Advanced retriever — MMR, hybrid BM25+semantic, multi-query, and contextual compression."""

import time
from typing import Optional

from loguru import logger

from langchain_core.documents import Document


class AdvancedRetriever:
    """Multi-strategy document retriever wrapping a VectorStoreManager.

    Supports: MMR, hybrid BM25+semantic, multi-query expansion,
    and LLM-based contextual compression.
    """

    def __init__(self, vector_store_manager, config: dict, llm=None) -> None:
        """Initialise with a VectorStoreManager, config, and optional LLM.

        Args:
            vector_store_manager: Initialised VectorStoreManager instance.
            config: Full application config dict.
            llm: Optional LangChain LLM for multi-query and compression.
        """
        self.vsm = vector_store_manager
        self.config = config
        self.llm = llm
        retrieval_cfg = config.get("retrieval", {})
        self.search_type: str = retrieval_cfg.get("search_type", "mmr")
        self.score_threshold: float = retrieval_cfg.get("score_threshold", 0.3)
        self.top_k: int = config.get("vector_store", {}).get("top_k", 5)
        self._retrieval_count: int = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Primary retrieval
    # ─────────────────────────────────────────────────────────────────────────

    def get_relevant_documents(self, query: str) -> list[Document]:
        """Retrieve the most relevant chunks for a query using MMR.

        Args:
            query: User's natural-language question.

        Returns:
            List of relevant Document chunks.
        """
        start = time.time()
        docs = self.vsm.mmr_search(query, k=self.top_k)
        elapsed_ms = (time.time() - start) * 1000
        self._retrieval_count += 1
        logger.debug(f"Retrieved {len(docs)} chunks for query in {elapsed_ms:.1f} ms.")
        return docs

    def hybrid_search(self, query: str) -> list[Document]:
        """Combine semantic similarity search with BM25 keyword search.

        Falls back to pure semantic search if rank_bm25 is not installed.

        Args:
            query: User's natural-language question.

        Returns:
            Re-ranked combined document list.
        """
        semantic_docs = self.vsm.mmr_search(query, k=self.top_k * 2)

        try:
            from rank_bm25 import BM25Okapi

            # Build BM25 corpus from retrieved candidates (fast, no extra index needed)
            corpus = [d.page_content for d in semantic_docs]
            tokenized = [doc.split() for doc in corpus]
            bm25 = BM25Okapi(tokenized)
            bm25_scores = bm25.get_scores(query.split())

            # Combine scores (0.6 semantic weight + 0.4 BM25 weight)
            scored = []
            for i, doc in enumerate(semantic_docs):
                combined = 0.6 * (i / max(len(semantic_docs), 1)) + 0.4 * bm25_scores[i]
                scored.append((combined, doc))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [doc for _, doc in scored[: self.top_k]]

        except ImportError:
            logger.debug("rank_bm25 not installed — using pure semantic search for hybrid_search.")
            return semantic_docs[: self.top_k]

    def contextual_compression(self, query: str, docs: list[Document]) -> list[Document]:
        """Use LLM to extract only the relevant portion from each document.

        Requires an LLM to be set. Falls back to original docs if not available.

        Args:
            query: The user query.
            docs: Retrieved document chunks.

        Returns:
            Compressed documents containing only query-relevant content.
        """
        if self.llm is None:
            return docs

        try:
            from langchain_classic.retrievers.document_compressors import LLMChainExtractor
            from langchain_classic.retrievers import ContextualCompressionRetriever

            compressor = LLMChainExtractor.from_llm(self.llm)
            base_retriever = self.vsm.get_retriever(self.search_type)
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever,
            )
            return compression_retriever.get_relevant_documents(query)
        except Exception as exc:
            logger.warning(f"Contextual compression failed ({exc}), returning original docs.")
            return docs

    def multi_query_retrieval(self, query: str) -> list[Document]:
        """Generate query variations and merge retrieved results.

        Generates 3 rephrased versions of the query, retrieves documents
        for each, and returns a deduplicated union.

        Args:
            query: Original user question.

        Returns:
            Deduplicated list of documents retrieved across all query variants.
        """
        queries = [query]

        if self.llm is not None:
            try:
                from langchain_classic.retrievers import MultiQueryRetriever

                mq_retriever = MultiQueryRetriever.from_llm(
                    retriever=self.vsm.get_retriever(self.search_type),
                    llm=self.llm,
                )
                return mq_retriever.get_relevant_documents(query)
            except Exception as exc:
                logger.warning(f"MultiQueryRetriever failed ({exc}), using single query.")

        return self.get_relevant_documents(query)

    # ─────────────────────────────────────────────────────────────────────────
    # Context formatting
    # ─────────────────────────────────────────────────────────────────────────

    def format_docs_for_context(self, docs: list[Document]) -> str:
        """Format a list of Document chunks into a clean context string.

        Args:
            docs: Retrieved document chunks.

        Returns:
            Formatted context string with source metadata.
        """
        if not docs:
            return "No relevant documents found."

        parts = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata
            source = meta.get("filename", meta.get("source", "Unknown"))
            page = meta.get("page", meta.get("slide", meta.get("section", "")))
            page_str = f" | Page {page}" if page else ""
            header = f"[Source {i}: {source}{page_str}]"
            parts.append(f"{header}\n{doc.page_content.strip()}")

        return "\n\n---\n\n".join(parts)

    # ─────────────────────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────────────────────

    def get_retrieval_stats(self, query: str, docs: list[Document]) -> dict:
        """Return a stats dict for a single retrieval operation.

        Args:
            query: The query that was executed.
            docs: The retrieved documents.

        Returns:
            Stats dict with query, count, sources, and retrieval time.
        """
        sources = list({d.metadata.get("filename", "unknown") for d in docs})
        return {
            "query": query,
            "num_retrieved": len(docs),
            "sources_used": sources,
            "total_retrievals": self._retrieval_count,
        }
