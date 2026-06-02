"""Tests for Linear SVM (from scratch)."""

from __future__ import annotations

import numpy as np

from linux_doctor.ml.linear_svm import LinearSVM


class TestLinearSVM:
    def test_fit_creates_classes(self):
        X = np.array([[1, 0], [0, 1], [0, -1]], dtype=np.float64)
        y = ["a", "b", "c"]
        svm = LinearSVM(n_iterations=50).fit(X, y)
        assert len(svm.classes_) == 3

    def test_predict_returns_labels(self):
        X = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]], dtype=np.float64)
        y = ["a", "b", "c"]
        svm = LinearSVM(n_iterations=100).fit(X, y)
        preds = svm.predict(X)
        assert preds == ["a", "b", "c"]

    def test_decision_function_shape(self):
        X = np.array([[1, 0], [0, 1]], dtype=np.float64)
        y = ["a", "b"]
        svm = LinearSVM(n_iterations=50).fit(X, y)
        scores = svm.decision_function(np.array([[0, 1]], dtype=np.float64))
        assert scores.shape == (1, 2)

    def test_predict_proba_output(self):
        X = np.array([[1, 0], [0, 1]], dtype=np.float64)
        y = ["x", "y"]
        svm = LinearSVM(n_iterations=100).fit(X, y)
        probs = svm.predict_proba(np.array([[0, 1]], dtype=np.float64))
        assert abs(probs.sum() - 1.0) < 0.001

    def test_binary_labels(self):
        y_idx = np.array([0, 1, 0, 1])
        binary = LinearSVM._binary_labels(y_idx, target_class=0)
        assert list(binary) == [1.0, -1.0, 1.0, -1.0]
