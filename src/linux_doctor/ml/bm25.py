"""
BM25 Retrieval Engine — From scratch, zero dependencies.

Okapi BM25 for document retrieval over Knowledge Base rules and past incidents.

Formulas:
    idf(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
    score(D, Q) = Σ idf(t) × (tf(t,D) × (k1 + 1)) / (tf(t,D) + k1 × (1 - b + b × |D|/avgdl))
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class BM25Document:
    """A document indexed by BM25."""
    id: str
    text: str
    domain: str | None = None


@dataclass
class BM25Result:
    """Search result with relevance score."""
    document_id: str
    score: float
    domain: str | None = None


class BM25:
    """
    Okapi BM25 retrieval engine.

    Usage:
        bm25 = BM25(k1=1.5, b=0.75)
        bm25.index(documents)
        results = bm25.search("nginx failed to start")
        top = results[:3]
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list[BM25Document] = []
        self._corpus: list[list[str]] = []
        self._avg_doc_len: float = 0.0
        self._idf: dict[str, float] = {}
        self._is_indexed: bool = False

    # ------------------------------------------------------------------
    # TOKENIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Tokenize text into lowercase terms."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text.split() if text else []

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------

    def index(self, documents: list[BM25Document]) -> BM25:
        """Build BM25 index from documents."""
        self._documents = documents
        self._corpus = [self.tokenize(d.text) for d in documents]
        n_docs = len(self._corpus)

        if n_docs == 0:
            self._avg_doc_len = 0.0
            self._idf = {}
            self._is_indexed = True
            return self

        self._avg_doc_len = sum(len(doc) for doc in self._corpus) / n_docs

        # Compute document frequency
        doc_freq: Counter[str] = Counter()
        for tokens in self._corpus:
            doc_freq.update(set(tokens))

        # Compute IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        self._idf = {}
        for term, df in doc_freq.items():
            self._idf[term] = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)

        self._is_indexed = True
        return self

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> list[BM25Result]:
        """
        Search for documents matching the query.

        Args:
            query: Natural language query
            top_k: Number of results to return

        Returns:
            List of BM25Result sorted by score descending
        """
        if not self._is_indexed or not self._documents:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        results: list[BM25Result] = []

        for i, doc in enumerate(self._documents):
            score = self._score(query_tokens, i)
            if score > 0:
                results.append(BM25Result(
                    document_id=doc.id,
                    score=round(score, 4),
                    domain=doc.domain,
                ))

        results.sort(key=lambda r: -r.score)
        return results[:top_k]

    def _score(self, query_tokens: list[str], doc_index: int) -> float:
        """Compute BM25 score for a single document."""
        doc_tokens = self._corpus[doc_index]
        doc_len = len(doc_tokens)
        doc_term_counts = Counter(doc_tokens)

        score = 0.0
        for term in query_tokens:
            tf = doc_term_counts.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf.get(term, 0)
            if idf == 0:
                continue

            # BM25 scoring
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_len)
            score += idf * numerator / denominator

        return score

    # ------------------------------------------------------------------
    # UTILITY
    # ------------------------------------------------------------------

    @property
    def doc_count(self) -> int:
        return len(self._documents)

    @property
    def vocab_size(self) -> int:
        return len(self._idf)

    def clear(self) -> None:
        """Clear the index."""
        self._documents = []
        self._corpus = []
        self._idf = {}
        self._is_indexed = False
