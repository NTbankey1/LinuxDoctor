"""Tests for the BM25 retrieval engine."""

from __future__ import annotations

import pytest

from linux_doctor.ml.bm25 import BM25, BM25Document


class TestBM25:
    @pytest.fixture
    def bm25(self):
        b = BM25(k1=1.5, b=0.75)
        docs = [
            BM25Document(id="nginx_001", text="nginx failed to start address already in use port 80 conflict",
                         domain="nginx"),
            BM25Document(id="docker_001", text="docker permission denied cannot connect to docker daemon socket",
                         domain="docker"),
            BM25Document(id="ssh_001", text="ssh connection refused port 22 sshd not running",
                         domain="ssh"),
        ]
        b.index(docs)
        return b

    def test_search_returns_results(self, bm25):
        assert len(bm25.search("nginx failed to start")) > 0

    def test_top_result_correct_domain(self, bm25):
        results = bm25.search("nginx failed to start")
        assert results[0].domain == "nginx"

    def test_top_result_docker(self, bm25):
        results = bm25.search("docker permission denied")
        assert results[0].domain == "docker"

    def test_search_no_match(self, bm25):
        assert len(bm25.search("weather forecast sunny")) == 0

    def test_scores_descending(self, bm25):
        results = bm25.search("port 80 conflict")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_index(self):
        assert len(BM25().search("test")) == 0

    def test_clear_index(self, bm25):
        bm25.clear()
        assert bm25.doc_count == 0
        assert len(bm25.search("nginx")) == 0

    def test_tokenize(self):
        tokens = BM25.tokenize("nginx failed to start on port 80")
        assert len(tokens) > 0
