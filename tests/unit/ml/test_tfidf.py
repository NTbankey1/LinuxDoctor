"""Tests for TF-IDF vectorizer (from scratch)."""

from __future__ import annotations

import numpy as np

from linux_doctor.ml.tfidf_engine import TFIDFVectorizer


class TestTFIDFVectorizer:
    def test_fit_creates_vocabulary(self):
        corpus = [["nginx", "failed", "start"], ["docker", "run", "error"]]
        v = TFIDFVectorizer().fit(corpus)
        assert v.vocab_size > 0

    def test_transform_returns_matrix(self):
        corpus = [["nginx", "failed"], ["docker", "error"]]
        v = TFIDFVectorizer().fit(corpus)
        X = v.transform([["nginx"]])
        assert isinstance(X, np.ndarray)
        assert X.shape[0] == 1

    def test_fit_transform_shape(self):
        corpus = [["nginx", "failed", "start"], ["docker", "run", "error"]]
        v = TFIDFVectorizer(max_features=100)
        X = v.fit_transform(corpus)
        assert X.shape[0] == 2
        assert X.shape[1] > 0

    def test_l2_normalization(self):
        corpus = [["nginx", "nginx", "nginx"], ["docker", "error"]]
        v = TFIDFVectorizer(max_features=100)
        X = v.fit_transform(corpus)
        # Each row should have unit norm
        norms = np.linalg.norm(X, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)

    def test_empty_corpus(self):
        v = TFIDFVectorizer()
        X = v.fit_transform([])
        assert X.size == 0

    def test_min_df_filtering(self):
        corpus = [["rare_term"], ["common_term"], ["common_term"]]
        v = TFIDFVectorizer(min_df=2)
        v.fit_transform(corpus)
        # "rare_term" appears in only 1 doc, should be filtered by min_df=2
        assert "rare_term" not in v.vocabulary_

    def test_transform_before_fit_raises(self):
        import pytest
        v = TFIDFVectorizer()
        with pytest.raises(RuntimeError):
            v.transform([["test"]])
