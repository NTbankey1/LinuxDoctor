"""
TF-IDF Engine — Phase 2.

Implements Term Frequency-Inverse Document Frequency from scratch using NumPy.

Formulas:
    tf(t, d)     = count(t in d) / |d|
    idf(t, D)    = log((|D| + 1) / (df(t) + 1)) + 1   [smooth IDF]
    tfidf(t,d,D) = tf(t, d) × idf(t, D)

Complexity:
    Fit:      O(N × L)  — N docs, L avg doc length
    Transform: O(N × V)  — V = vocabulary size
"""

import math
from collections import Counter

import numpy as np


class TFIDFVectorizer:
    """
    Manual TF-IDF Vectorizer.

    Usage:
        vectorizer = TFIDFVectorizer(max_features=5000)
        X_train = vectorizer.fit_transform(train_docs)
        X_test  = vectorizer.transform(test_docs)
    """

    def __init__(self, max_features: int = 5000, min_df: int = 1) -> None:
        """
        Initialize the vectorizer.

        Args:
            max_features: Keep only top-N terms by total TF-IDF score.
            min_df: Ignore terms that appear in fewer than min_df documents.
        """
        self.max_features = max_features
        self.min_df = min_df

        # Set after fit()
        self.vocabulary_: dict[str, int] = {}     # term → column index
        self.idf_: dict[str, float] = {}          # term → IDF value
        self._n_docs: int = 0

    # ------------------------------------------------------------------
    # STEP 1: Compute Term Frequencies for a single document
    # ------------------------------------------------------------------

    @staticmethod
    def _term_freq(tokens: list[str]) -> dict[str, float]:
        """
        Compute TF for all terms in a document.

        tf(t, d) = count(t in d) / |d|

        Args:
            tokens: List of preprocessed tokens.

        Returns:
            Dict mapping each term to its TF value.
        """
        counts = Counter(tokens)
        total = len(tokens)
        if total == 0:
            return {}
        return {term: count / total for term, count in counts.items()}

    # ------------------------------------------------------------------
    # STEP 2: Compute Inverse Document Frequency over the corpus
    # ------------------------------------------------------------------

    def _compute_idf(self, corpus_tokens: list[list[str]]) -> None:
        """
        Compute and store IDF values for all terms.

        idf(t, D) = log((N + 1) / (df(t) + 1)) + 1   [Scikit-learn smooth]

        Args:
            corpus_tokens: List of token-lists (one per document).
        """
        n_docs = len(corpus_tokens)
        self._n_docs = n_docs

        # df(t): number of documents that contain term t
        doc_freq: Counter[str] = Counter()
        for tokens in corpus_tokens:
            doc_freq.update(set(tokens))  # set() → count each doc once

        # Compute smooth IDF
        idf_raw: dict[str, float] = {}
        for term, df in doc_freq.items():
            if df < self.min_df:
                continue
            idf_raw[term] = math.log((n_docs + 1) / (df + 1)) + 1.0

        # Prune to max_features (keep terms with highest IDF × total count)
        if len(idf_raw) > self.max_features:
            # Sort by IDF descending (rare terms first), keep top N
            sorted_terms = sorted(idf_raw, key=idf_raw.__getitem__, reverse=True)
            idf_raw = {t: idf_raw[t] for t in sorted_terms[: self.max_features]}

        self.idf_ = idf_raw
        # Build vocabulary index (alphabetical for reproducibility)
        self.vocabulary_ = {term: idx for idx, term in enumerate(sorted(idf_raw))}

    # ------------------------------------------------------------------
    # STEP 3: Build TF-IDF matrix for a set of documents
    # ------------------------------------------------------------------

    def _tfidf_matrix(self, corpus_tokens: list[list[str]]) -> np.ndarray:
        """
        Build the TF-IDF feature matrix.

        Shape: (n_docs, vocab_size)

        Args:
            corpus_tokens: List of token-lists.

        Returns:
            Float64 NumPy array of shape (N, V).
        """
        n = len(corpus_tokens)
        v = len(self.vocabulary_)
        matrix = np.zeros((n, v), dtype=np.float64)

        for i, tokens in enumerate(corpus_tokens):
            tf = self._term_freq(tokens)
            for term, tf_val in tf.items():
                if term in self.vocabulary_:
                    col = self.vocabulary_[term]
                    idf_val = self.idf_[term]
                    matrix[i, col] = tf_val * idf_val

        # L2-normalize each row so cosine similarity works correctly
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # avoid division by zero for zero vectors
        return matrix / norms

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def fit(self, corpus_tokens: list[list[str]]) -> "TFIDFVectorizer":
        """
        Learn vocabulary and IDF weights from corpus.

        Args:
            corpus_tokens: Training corpus as list of token lists.

        Returns:
            self (for chaining)
        """
        self._compute_idf(corpus_tokens)
        return self

    def transform(self, corpus_tokens: list[list[str]]) -> np.ndarray:
        """
        Transform documents into TF-IDF feature vectors.

        Args:
            corpus_tokens: Documents as list of token lists.

        Returns:
            NumPy array of shape (n_docs, vocab_size).
        """
        if not self.vocabulary_:
            raise RuntimeError("Call fit() before transform().")
        return self._tfidf_matrix(corpus_tokens)

    def fit_transform(self, corpus_tokens: list[list[str]]) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(corpus_tokens)
        if not self.vocabulary_:
            return np.zeros((len(corpus_tokens), 0), dtype=np.float64)
        return self.transform(corpus_tokens)

    @property
    def vocab_size(self) -> int:
        """Return the number of terms in vocabulary."""
        return len(self.vocabulary_)
