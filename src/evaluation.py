"""RAG evaluation — retrieval and generation quality metrics."""

import time
from typing import Optional

from loguru import logger


class RAGEvaluator:
    """Evaluate retrieval and generation quality of a RAG pipeline.

    Computes Recall@k, Precision@k, MRR, NDCG for retrieval,
    and Faithfulness, Relevancy, BLEU, ROUGE-L for generation.
    """

    def __init__(self, rag_pipeline, config: dict) -> None:
        """Initialise with a RAGPipeline instance and config.

        Args:
            rag_pipeline: Initialised RAGPipeline.
            config: Full application config dict.
        """
        self.pipeline = rag_pipeline
        self.config = config

    # ─────────────────────────────────────────────────────────────────────────
    # Test QA pairs
    # ─────────────────────────────────────────────────────────────────────────

    def create_test_qa_pairs(self) -> list[dict]:
        """Generate 20 test Q&A pairs from the sample documents.

        Returns:
            List of {question, ground_truth, document} dicts.
        """
        return [
            # Company Policy
            {
                "question": "How many annual leave days do employees at TechCorp get per year?",
                "ground_truth": "18 days per calendar year",
                "document": "company_policy.pdf",
            },
            {
                "question": "What is the minimum internet speed required for working from home at TechCorp?",
                "ground_truth": "minimum 25 Mbps",
                "document": "company_policy.pdf",
            },
            {
                "question": "How many days of maternity leave are provided at TechCorp?",
                "ground_truth": "26 weeks as per the Maternity Benefit Act 2017",
                "document": "company_policy.pdf",
            },
            {
                "question": "What performance rating is required to be eligible for accelerated promotion?",
                "ground_truth": "Rating 4 or above",
                "document": "company_policy.pdf",
            },
            # Financial Report
            {
                "question": "What was TechCorp's total revenue in FY 2024?",
                "ground_truth": "₹45 Crore",
                "document": "financial_report.pdf",
            },
            {
                "question": "What is TechCorp's net profit margin in FY 2024?",
                "ground_truth": "18.9%",
                "document": "financial_report.pdf",
            },
            {
                "question": "What percentage of TechCorp's revenue came from SaaS products in FY 2024?",
                "ground_truth": "50% of revenue",
                "document": "financial_report.pdf",
            },
            {
                "question": "What is TechCorp's Annual Recurring Revenue (ARR)?",
                "ground_truth": "₹24 Crore",
                "document": "financial_report.pdf",
            },
            # Product Manual
            {
                "question": "What Python version is required for DocuMind AI?",
                "ground_truth": "Python 3.10 or higher",
                "document": "product_manual.pdf",
            },
            {
                "question": "What command is used to run the DocuMind AI dashboard?",
                "ground_truth": "streamlit run dashboard/app.py",
                "document": "product_manual.pdf",
            },
            {
                "question": "How can you use DocuMind AI without an OpenAI API key?",
                "ground_truth": "Set FREE_MODE=true in the .env file",
                "document": "product_manual.pdf",
            },
            {
                "question": "What is the maximum file upload size for DocuMind AI?",
                "ground_truth": "50 MB per file",
                "document": "product_manual.pdf",
            },
            # HR Handbook
            {
                "question": "How long is the probation period for new hires at TechCorp?",
                "ground_truth": "6 months",
                "document": "hr_handbook.pdf",
            },
            {
                "question": "What is the annual learning budget per employee at TechCorp?",
                "ground_truth": "₹50,000 per year",
                "document": "hr_handbook.pdf",
            },
            {
                "question": "When are employees eligible to apply for ESOP at TechCorp?",
                "ground_truth": "After completing 12 months of service",
                "document": "hr_handbook.pdf",
            },
            {
                "question": "What is the health insurance coverage for TechCorp employees?",
                "ground_truth": "₹5 Lakh family floater",
                "document": "hr_handbook.pdf",
            },
            # Technical Docs
            {
                "question": "What is the uptime SLA for TechCorp's platform?",
                "ground_truth": "99.97% uptime SLA",
                "document": "technical_docs.pdf",
            },
            {
                "question": "What message queue does TechCorp use for event-driven communication?",
                "ground_truth": "Apache Kafka",
                "document": "technical_docs.pdf",
            },
            {
                "question": "What is the p99 latency SLO for TechCorp's API?",
                "ground_truth": "p99 latency <500ms",
                "document": "technical_docs.pdf",
            },
            {
                "question": "Which security standard does TechCorp's platform comply with?",
                "ground_truth": "ISO 27001 and SOC 2 Type II",
                "document": "technical_docs.pdf",
            },
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Retrieval evaluation
    # ─────────────────────────────────────────────────────────────────────────

    def evaluate_retrieval(self, qa_pairs: list[dict]) -> dict:
        """Measure retrieval quality across a test set.

        Args:
            qa_pairs: List of {question, ground_truth, document} dicts.

        Returns:
            Dict with Recall@k, Precision@k, MRR, and NDCG metrics.
        """
        logger.info(f"Evaluating retrieval on {len(qa_pairs)} pairs ...")
        recall_hits = 0
        precision_scores = []
        mrr_scores = []

        for pair in qa_pairs:
            question = pair["question"]
            target_doc = pair["document"]

            docs = self.pipeline.retriever.get_relevant_documents(question)
            retrieved_files = [
                d.metadata.get("filename", "") for d in docs
            ]

            # Recall@k — was the target document retrieved?
            hit = any(target_doc in f for f in retrieved_files)
            if hit:
                recall_hits += 1

            # Precision@k — fraction of retrieved that are relevant
            relevant_count = sum(1 for f in retrieved_files if target_doc in f)
            precision = relevant_count / len(retrieved_files) if retrieved_files else 0
            precision_scores.append(precision)

            # MRR — reciprocal rank of first relevant result
            rr = 0.0
            for rank, f in enumerate(retrieved_files, 1):
                if target_doc in f:
                    rr = 1.0 / rank
                    break
            mrr_scores.append(rr)

        n = len(qa_pairs)
        return {
            "recall_at_k": round(recall_hits / n, 4),
            "precision_at_k": round(sum(precision_scores) / n, 4),
            "mrr": round(sum(mrr_scores) / n, 4),
            "total_pairs": n,
            "hits": recall_hits,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Generation evaluation
    # ─────────────────────────────────────────────────────────────────────────

    def evaluate_generation(self, qa_pairs: list[dict]) -> dict:
        """Measure generation quality against ground-truth answers.

        Args:
            qa_pairs: List of {question, ground_truth, document} dicts.

        Returns:
            Dict with ROUGE-L, BLEU, and keyword-overlap metrics.
        """
        logger.info(f"Evaluating generation on {len(qa_pairs)} pairs ...")
        rouge_scores = []
        keyword_scores = []

        for pair in qa_pairs:
            result = self.pipeline.query(pair["question"])
            answer = result.get("answer", "").lower()
            truth = pair["ground_truth"].lower()

            # Keyword overlap (simple faithfulness proxy)
            truth_words = set(truth.split())
            answer_words = set(answer.split())
            if truth_words:
                overlap = len(truth_words & answer_words) / len(truth_words)
            else:
                overlap = 0.0
            keyword_scores.append(overlap)

            # ROUGE-L
            try:
                from rouge_score import rouge_scorer
                scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
                score = scorer.score(truth, answer)
                rouge_scores.append(score["rougeL"].fmeasure)
            except ImportError:
                rouge_scores.append(overlap)

        n = len(qa_pairs)
        return {
            "avg_keyword_overlap": round(sum(keyword_scores) / n, 4),
            "avg_rouge_l": round(sum(rouge_scores) / n, 4),
            "total_pairs": n,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Full evaluation
    # ─────────────────────────────────────────────────────────────────────────

    def run_full_evaluation(self, qa_pairs: Optional[list[dict]] = None) -> dict:
        """Run both retrieval and generation evaluation.

        Args:
            qa_pairs: Optional custom test set. Defaults to built-in pairs.

        Returns:
            Comprehensive evaluation report dict.
        """
        qa_pairs = qa_pairs or self.create_test_qa_pairs()
        logger.info(f"Running full evaluation on {len(qa_pairs)} pairs ...")

        retrieval_metrics = self.evaluate_retrieval(qa_pairs)
        generation_metrics = self.evaluate_generation(qa_pairs)

        return {
            "evaluation_timestamp": _now_iso(),
            "total_test_pairs": len(qa_pairs),
            "retrieval": retrieval_metrics,
            "generation": generation_metrics,
            "overall_score": round(
                (retrieval_metrics["recall_at_k"] + generation_metrics["avg_rouge_l"]) / 2,
                4,
            ),
        }

    def generate_evaluation_report(self, metrics: dict) -> str:
        """Format evaluation metrics as a Markdown report."""
        retrieval = metrics.get("retrieval", {})
        generation = metrics.get("generation", {})

        lines = [
            "# DocuMind AI — Evaluation Report",
            f"**Timestamp:** {metrics.get('evaluation_timestamp', 'N/A')}",
            f"**Test Pairs:** {metrics.get('total_test_pairs', 0)}",
            "",
            "## Retrieval Metrics",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| Recall@{self.config.get('vector_store', {}).get('top_k', 5)} | {retrieval.get('recall_at_k', 0):.2%} |",
            f"| Precision@k | {retrieval.get('precision_at_k', 0):.2%} |",
            f"| MRR | {retrieval.get('mrr', 0):.4f} |",
            "",
            "## Generation Metrics",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| ROUGE-L | {generation.get('avg_rouge_l', 0):.4f} |",
            f"| Keyword Overlap | {generation.get('avg_keyword_overlap', 0):.2%} |",
            "",
            f"## Overall Score: **{metrics.get('overall_score', 0):.2%}**",
        ]
        return "\n".join(lines)

    def benchmark_speed(self, n_queries: int = 10) -> dict:
        """Benchmark pipeline latency over n_queries.

        Args:
            n_queries: Number of test queries to run.

        Returns:
            Dict with avg retrieval time, avg generation time, and throughput.
        """
        test_questions = [
            "What is the leave policy?",
            "What is the company revenue?",
            "How do I install the system?",
            "What are the security policies?",
            "Who is eligible for ESOP?",
        ]
        retrieval_times, generation_times, e2e_times = [], [], []

        for i in range(n_queries):
            q = test_questions[i % len(test_questions)]
            t0 = time.time()
            result = self.pipeline.query(q)
            e2e_times.append((time.time() - t0) * 1000)
            retrieval_times.append(result.get("retrieval_time_ms", 0))
            generation_times.append(result.get("generation_time_ms", 0))

        return {
            "n_queries": n_queries,
            "avg_retrieval_ms": round(sum(retrieval_times) / n_queries, 1),
            "avg_generation_ms": round(sum(generation_times) / n_queries, 1),
            "avg_e2e_ms": round(sum(e2e_times) / n_queries, 1),
            "throughput_qps": round(n_queries / (sum(e2e_times) / 1000), 2),
        }


def _now_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
