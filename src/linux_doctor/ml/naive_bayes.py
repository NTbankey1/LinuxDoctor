"""
Multinomial Naive Bayes — Phase 3.

Implements multi-class Naive Bayes from scratch using NumPy.

Mathematical Foundation:
    Bayes Theorem:
        P(c | d) ∝ P(c) × P(d | c)

    Log-space (avoid float underflow):
        log P(c | d) = log P(c) + Σ tf(t,d) × log P(t|c)
                                   t∈d

    Laplace Smoothing (α = 1):
        P(t | c) = (count(t,c) + α) / (Σ count(t',c) + α × |V|)
                                        t'

    This prevents P(t|c) = 0 for unseen terms.
"""

import numpy as np


class MultinomialNaiveBayes:
    """
    Multi-class Multinomial Naive Bayes classifier (from scratch).

    Designed for TF-IDF feature vectors where each feature represents
    a term weight in a document.
    """

    def __init__(self, alpha: float = 1.0) -> None:
        """
        Initialize the classifier.

        Args:
            alpha: Laplace smoothing parameter (default 1.0).
        """
        self.alpha = alpha

        # Set after fit()
        self.classes_: list[str] = []
        self._log_priors: np.ndarray = np.array([])       # shape: (n_classes,)
        self._log_likelihoods: np.ndarray = np.array([])  # shape: (n_classes, n_features)

    def fit(self, X: np.ndarray, y: list[str]) -> "MultinomialNaiveBayes":
        """
        Train the Naive Bayes classifier.

        Steps:
            1. Compute class priors: log P(c) = log(count_c / N)
            2. Compute term likelihoods with Laplace smoothing
            3. Store as log-probabilities for numerical stability

        Args:
            X: Feature matrix (N × V), TF-IDF weights.
            y: List of N string class labels.

        Returns:
            self
        """
        n_samples, n_features = X.shape
        self.classes_ = sorted(set(y))
        n_classes = len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        # Convert labels to indices
        y_idx = np.array([class_to_idx[label] for label in y])

        # 1. Class priors: P(c) = count_c / N
        #    log P(c) to avoid underflow
        class_counts = np.zeros(n_classes, dtype=np.float64)
        for idx in y_idx:
            class_counts[idx] += 1.0
        self._log_priors = np.log(class_counts / n_samples)

        # 2. Term likelihoods: P(t | c) with Laplace smoothing
        #    Sum of TF-IDF weights per class per feature
        #    Shape: (n_classes, n_features)
        feature_counts = np.zeros((n_classes, n_features), dtype=np.float64)
        for i, label_idx in enumerate(y_idx):
            feature_counts[label_idx] += X[i]

        # Laplace: add alpha to every cell
        feature_counts += self.alpha

        # Row sum (total feature weight per class) + smoothing
        row_sums = feature_counts.sum(axis=1, keepdims=True)

        # log P(t | c)
        self._log_likelihoods = np.log(feature_counts / row_sums)

        return self

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute log posterior probabilities.

        log P(c | d) = log P(c) + Σ X[t] × log P(t | c)
                                    t

        Args:
            X: Feature matrix (M × V) for M test documents.

        Returns:
            Log-probability matrix (M × n_classes).
        """
        # (M, V) @ (V, C) + (C,) → (M, C)
        return X @ self._log_likelihoods.T + self._log_priors

    def predict(self, X: np.ndarray) -> list[str]:
        """
        Predict class labels for each document.

        Args:
            X: Feature matrix (M × V).

        Returns:
            List of M predicted class labels.
        """
        log_probs = self.predict_log_proba(X)
        best_indices = np.argmax(log_probs, axis=1)
        return [self.classes_[i] for i in best_indices]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute normalized posterior probabilities via softmax.

        Args:
            X: Feature matrix (M × V).

        Returns:
            Probability matrix (M × n_classes), rows sum to 1.
        """
        log_probs = self.predict_log_proba(X)
        # Softmax in log-space for numerical stability
        log_probs -= log_probs.max(axis=1, keepdims=True)
        probs = np.exp(log_probs)
        return probs / probs.sum(axis=1, keepdims=True)
