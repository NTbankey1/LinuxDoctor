"""Tests for Multinomial Naive Bayes (from scratch)."""

from __future__ import annotations

import numpy as np

from linux_doctor.ml.naive_bayes import MultinomialNaiveBayes


class TestMultinomialNaiveBayes:
    def test_fit_creates_classes(self):
        X = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float64)
        y = ["a", "b", "c"]
        nb = MultinomialNaiveBayes().fit(X, y)
        assert nb.classes_ == ["a", "b", "c"]

    def test_predict_returns_labels(self):
        X = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]], dtype=np.float64)
        y = ["a", "b", "c"]
        nb = MultinomialNaiveBayes().fit(X, y)
        preds = nb.predict(X)
        assert preds == ["a", "b", "c"]

    def test_predict_proba_shape(self):
        X = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float64)
        y = ["a", "b"]
        nb = MultinomialNaiveBayes().fit(X, y)
        probs = nb.predict_proba(np.array([[0, 1, 0]], dtype=np.float64))
        assert probs.shape == (1, 2)
        assert abs(probs.sum() - 1.0) < 0.001

    def test_laplace_smoothing(self):
        """Should not crash with zero probabilities for unseen features."""
        X_train = np.array([[1, 0, 1], [0, 1, 0]], dtype=np.float64)
        y = ["a", "b"]
        nb = MultinomialNaiveBayes(alpha=1.0).fit(X_train, y)
        X_test = np.array([[0, 0, 1]], dtype=np.float64)
        probs = nb.predict_proba(X_test)
        assert not np.any(np.isnan(probs))
        assert not np.any(np.isinf(probs))

    def test_log_probas_are_negative(self):
        X = np.array([[1, 0], [0, 1]], dtype=np.float64)
        y = ["x", "y"]
        nb = MultinomialNaiveBayes().fit(X, y)
        log_probs = nb.predict_log_proba(np.array([[0, 1]], dtype=np.float64))
        assert (log_probs < 0).all()

    def test_alpha_default(self):
        nb = MultinomialNaiveBayes()
        assert nb.alpha == 1.0

    def test_alpha_custom(self):
        nb = MultinomialNaiveBayes(alpha=0.5)
        assert nb.alpha == 0.5
