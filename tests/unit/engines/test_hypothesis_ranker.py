"""Tests for the Bayesian hypothesis ranker."""

from __future__ import annotations

import pytest

from linux_doctor.engines.hypothesis_ranker import HypothesisRanker, ScoredHypothesis


class TestHypothesisRanker:
    @pytest.fixture
    def ranker(self):
        return HypothesisRanker()

    def test_posterior_increases_with_supporting_evidence(self, ranker):
        hypotheses = [{"id": "port_conflict_80", "description": "Port blocked", "confidence": 0.5}]
        facts = {"port_80_owner": "apache2"}
        result = ranker.evaluate_hypotheses(hypotheses, facts, "nginx")
        assert result.all_hypotheses[0].posterior_confidence > 0.5

    def test_posterior_decreases_without_evidence(self, ranker):
        hypotheses = [{"id": "port_conflict_80", "description": "Port blocked", "confidence": 0.8}]
        facts = {}
        result = ranker.evaluate_hypotheses(hypotheses, facts, "nginx")
        assert result.all_hypotheses[0].posterior_confidence < 0.8

    def test_single_hypothesis_conclusive(self, ranker):
        hypotheses = [{"id": "H1", "description": "Test", "confidence": 0.5}]
        result = ranker.evaluate_hypotheses(hypotheses, {"port_80_owner": "apache2"}, "test")
        assert result.is_conclusive is True

    def test_higher_confidence_wins(self, ranker):
        hypotheses = [
            {"id": "H1", "description": "Main cause", "confidence": 0.7},
            {"id": "H2", "description": "Unlikely cause", "confidence": 0.1},
        ]
        result = ranker.evaluate_hypotheses(hypotheses, {"port_80_owner": "apache2"}, "test")
        assert result.root_cause_id == "H1"

    def test_elimination_zeroes_confidence(self, ranker):
        hypotheses = [{"id": "sshd_not_running", "description": "SSHD down", "confidence": 0.8}]
        facts = {"sshd_status": "active"}
        result = ranker.evaluate_hypotheses(hypotheses, facts, "ssh")
        hyp = [h for h in result.all_hypotheses if h.hypothesis_id == "sshd_not_running"]
        assert hyp[0].posterior_confidence == 0.0 or hyp[0].is_eliminated

    def test_multiple_hypotheses_ranked(self, ranker):
        hypotheses = [
            {"id": "H1", "description": "Cause 1", "confidence": 0.6},
            {"id": "H2", "description": "Cause 2", "confidence": 0.3},
            {"id": "H3", "description": "Cause 3", "confidence": 0.1},
        ]
        result = ranker.evaluate_hypotheses(hypotheses, {"evidence": "present"}, "test")
        assert len(result.all_hypotheses) == 3

    def test_ranking_table_format(self, ranker):
        scored = [
            ScoredHypothesis("H1", "Cause 1", "test", 0.5, 0.8, "confirmed"),
            ScoredHypothesis("H2", "Cause 2", "test", 0.3, 0.0, "eliminated"),
        ]
        table = ranker.format_ranking_table(scored)
        assert len(table) == 2
        assert all("confidence" in row for row in table)
        assert all("status" in row for row in table)
