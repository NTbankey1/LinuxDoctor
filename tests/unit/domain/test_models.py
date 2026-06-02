"""Tests for domain models."""

from __future__ import annotations

from linux_doctor.domain.models import (
    CommandRecommendation,
    Diagnosis,
    Evidence,
    Fact,
    Hypothesis,
    HypothesisStatus,
    Session,
)


class TestFact:
    def test_create_fact(self):
        f = Fact(key="cpu_usage", value="95%", source="command")
        assert f.key == "cpu_usage"
        assert f.value == "95%"
        assert f.confidence == 1.0


class TestEvidence:
    def test_success_property(self):
        e = Evidence(command_run="test", stdout="ok", stderr="", return_code=0)
        assert e.is_success is True

    def test_failure_property(self):
        e = Evidence(command_run="test", stdout="", stderr="error", return_code=1)
        assert e.is_success is False


class TestHypothesis:
    def test_default_status(self):
        h = Hypothesis(id="H1", description="Test", domain="test")
        assert h.status == HypothesisStatus.PENDING

    def test_is_active(self):
        h = Hypothesis(id="H1", description="Test", domain="test")
        assert h.is_active is True

    def test_is_eliminated(self):
        h = Hypothesis(id="H1", description="Test", domain="test", status=HypothesisStatus.ELIMINATED)
        assert h.is_eliminated is True

    def test_is_confirmed(self):
        h = Hypothesis(id="H1", description="Test", domain="test", status=HypothesisStatus.CONFIRMED)
        assert h.is_confirmed is True


class TestCommandRecommendation:
    def test_default_risk(self):
        r = CommandRecommendation(command="echo test", explanation="test")
        assert r.risk == "moderate"
        assert r.is_safe_to_auto_run is False

    def test_safe_command(self):
        r = CommandRecommendation(command="echo test", explanation="test", risk="safe", is_safe_to_auto_run=True)
        assert r.is_safe_to_auto_run is True


class TestDiagnosis:
    def test_create_diagnosis(self, sample_diagnosis):
        assert sample_diagnosis.root_cause == "Port 80 occupied by apache2"
        assert sample_diagnosis.confidence == 0.95
        assert len(sample_diagnosis.recommended_fixes) == 1

    def test_inconclusive_diagnosis(self):
        d = Diagnosis(
            category="test", root_cause="Unknown", confidence=0.0,
            recommended_fixes=[], explanation="No conclusion",
            is_conclusive=False, margin=0.0,
        )
        assert d.is_conclusive is False


class TestSession:
    def test_new_session(self):
        s = Session()
        assert s.session_id is not None
        assert s.status == "active"

    def test_session_with_query(self):
        s = Session(user_query="nginx failed to start")
        assert s.user_query == "nginx failed to start"

    def test_session_diagnosis(self, sample_diagnosis):
        s = Session(user_query="test")
        s.diagnosis = sample_diagnosis
        assert s.diagnosis is not None
        assert s.diagnosis.root_cause == "Port 80 occupied by apache2"
