"""Tests for Logistic Regression (from scratch)."""

from __future__ import annotations

import numpy as np

from linux_doctor.ml.logistic_regression import LogisticRegression


class TestLogisticRegression:
    def test_fit_creates_classes(self):
        X = np.array([[1, 0], [0, 1], [0, -1]], dtype=np.float64)
        y = ["a", "b", "c"]
        lr = LogisticRegression(n_iterations=50, verbose=False).fit(X, y)
        assert len(lr.classes_) == 3

    def test_predict_returns_labels(self):
        X = np.array([[2, 0], [0, 2], [-2, 0]], dtype=np.float64)
        y = ["a", "b", "c"]
        lr = LogisticRegression(n_iterations=100, verbose=False).fit(X, y)
        preds = lr.predict(X)
        assert len(preds) == 3

    def test_predict_proba_sum_to_one(self):
        X = np.array([[1, 0], [0, 1]], dtype=np.float64)
        y = ["a", "b"]
        lr = LogisticRegression(n_iterations=100, verbose=False).fit(X, y)
        probs = lr.predict_proba(np.array([[0.5, 0.5]], dtype=np.float64))
        assert abs(probs.sum() - 1.0) < 0.001

    def test_predict_proba_shape(self):
        X = np.array([[1, 0], [0, 1]], dtype=np.float64)
        y = ["a", "b"]
        lr = LogisticRegression(n_iterations=50, verbose=False).fit(X, y)
        probs = lr.predict_proba(np.array([[1, 0]], dtype=np.float64))
        assert probs.shape == (1, 2)
