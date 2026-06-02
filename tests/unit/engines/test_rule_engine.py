"""Tests for the forward-chaining rule engine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from linux_doctor.domain.models import Session
from linux_doctor.engines.rule_engine import RuleEngine
from linux_doctor.infrastructure.kb_loader import RcaCondition


class TestSymptomMatching:
    @pytest.fixture
    def engine(self, docker_kb):
        return RuleEngine(kb=docker_kb)

    def test_docker_permission_matches(self, engine):
        matched = engine._match_symptoms("got permission denied trying to connect to docker.sock")
        assert any(r.rule_id == "DOCKER_001" for r in matched)

    def test_docker_no_match(self, engine):
        matched = engine._match_symptoms("weather report today")
        assert len(matched) == 0

    def test_multiple_rules_match(self, engine):
        matched = engine._match_symptoms("cannot connect to docker daemon permission denied")
        assert len(matched) >= 2


class TestConditionEvaluation:
    @pytest.fixture
    def engine(self, docker_kb):
        return RuleEngine(kb=docker_kb)

    def test_contains_true(self, engine):
        cond = RcaCondition(fact="user_groups", operator="contains", value="docker")
        assert engine._evaluate_condition(cond, {"user_groups": "sudo docker user"})

    def test_contains_false(self, engine):
        cond = RcaCondition(fact="user_groups", operator="contains", value="docker")
        assert not engine._evaluate_condition(cond, {"user_groups": "sudo user"})

    def test_not_contains_true(self, engine):
        cond = RcaCondition(fact="user_groups", operator="not_contains", value="docker")
        assert engine._evaluate_condition(cond, {"user_groups": "sudo user"})

    def test_equals_true(self, engine):
        cond = RcaCondition(fact="status", operator="equals", value="active")
        assert engine._evaluate_condition(cond, {"status": "active"})

    def test_equals_false(self, engine):
        cond = RcaCondition(fact="status", operator="equals", value="active")
        assert not engine._evaluate_condition(cond, {"status": "inactive"})

    def test_is_empty_true(self, engine):
        cond = RcaCondition(fact="port", operator="is_empty", value="")
        assert engine._evaluate_condition(cond, {"port": ""})

    def test_is_not_empty_true(self, engine):
        cond = RcaCondition(fact="port", operator="is_not_empty", value="")
        assert engine._evaluate_condition(cond, {"port": "apache2"})

    def test_greater_than_true(self, engine):
        cond = RcaCondition(fact="usage", operator="greater_than", value="90")
        assert engine._evaluate_condition(cond, {"usage": "95"})

    def test_greater_than_false(self, engine):
        cond = RcaCondition(fact="usage", operator="greater_than", value="90")
        assert not engine._evaluate_condition(cond, {"usage": "50"})

    def test_unknown_operator(self, engine):
        cond = RcaCondition(fact="x", operator="nonexistent", value="x")
        assert not engine._evaluate_condition(cond, {"x": "x"})


class TestMultiHopChaining:
    def test_reasoning_chain_has_steps(self, docker_kb, mock_executor):
        engine = RuleEngine(kb=docker_kb, executor=mock_executor)
        engine.diagnose(Session(user_query="docker permission denied"))
        assert len(engine.get_reasoning_chain().get_chain()) >= 2

    def test_symptom_step_recorded(self, ssh_kb):
        from linux_doctor.engines.reasoning_chain import ReasoningStepType
        engine = RuleEngine(kb=ssh_kb)
        with patch.object(engine.executor, "execute") as m:
            m.return_value = MagicMock(stdout="inactive", stderr="", return_code=0)
            engine.diagnose(Session(user_query="ssh connection refused"))
        steps = engine.get_reasoning_chain().get_chain()
        symptom_steps = [s for s in steps if s.step_type == ReasoningStepType.SYMPTOM_MATCHED]
        assert len(symptom_steps) >= 1

    def test_no_match_returns_none(self, docker_kb):
        engine = RuleEngine(kb=docker_kb)
        assert engine.diagnose(Session(user_query="weather report")) is None

    def test_template_resolution(self, docker_kb):
        engine = RuleEngine(kb=docker_kb)
        engine.facts = {"sshd_status": "inactive"}
        result = engine._resolve_template(
            "Status: {{sshd_status.sshd_status}}",
            {"sshd_status": "inactive"},
        )
        assert "inactive" in result


class TestEndToEndDiagnosis:
    def test_ssh_diagnosis_with_mock(self, ssh_kb):
        engine = RuleEngine(kb=ssh_kb)
        m = MagicMock()
        def side_effect(cmd):
            if "is-active" in cmd:
                return MagicMock(stdout="inactive", stderr="", return_code=3)
            if "ss -tulpn" in cmd or "netstat" in cmd:
                return MagicMock(stdout="NOT_LISTENING", stderr="", return_code=1)
            if "iptables" in cmd or "ufw" in cmd:
                return MagicMock(stdout="FIREWALL_CHECK_FAILED", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = side_effect
        engine.executor = m
        d = engine.diagnose(Session(user_query="ssh connection refused"))
        assert d is not None
        assert "sshd" in d.root_cause.lower() or "SSH" in d.root_cause
        assert len(d.recommended_fixes) > 0

    def test_docker_full_diagnosis(self, docker_kb):
        engine = RuleEngine(kb=docker_kb)
        m = MagicMock()
        def side_effect(cmd):
            if "groups" in cmd:
                return MagicMock(stdout="ntbankey sudo", stderr="", return_code=0)
            if "docker.sock" in cmd:
                return MagicMock(stdout="srw-rw---- 1 root docker", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = side_effect
        engine.executor = m
        d = engine.diagnose(Session(user_query="docker permission denied"))
        assert d is not None

    def test_nginx_port_conflict(self, nginx_kb):
        engine = RuleEngine(kb=nginx_kb)
        m = MagicMock()
        def side_effect(cmd):
            if ":80 " in cmd:
                return MagicMock(stdout='LISTEN users:(("apache2",pid=1234))', stderr="", return_code=0)
            if ":443 " in cmd:
                return MagicMock(stdout="", stderr="", return_code=0)
            if "nginx -t" in cmd:
                return MagicMock(stdout="syntax is ok", stderr="", return_code=0)
            if "status nginx" in cmd:
                return MagicMock(stdout="Active: failed", stderr="", return_code=3)
            # NGINX_006 evidence: nginx binary EXISTS
            if "command -v nginx" in cmd:
                return MagicMock(stdout="NGINX_BINARY_EXISTS", stderr="", return_code=0)
            if "rpm -q nginx" in cmd or "dpkg -l nginx" in cmd:
                return MagicMock(stdout="NGINX_PKG_INSTALLED", stderr="", return_code=0)
            if "systemctl list-unit-files nginx" in cmd:
                return MagicMock(stdout="NGINX_UNIT_EXISTS", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = side_effect
        engine.executor = m
        d = engine.diagnose(Session(user_query="nginx failed to start"))
        assert d is not None
        assert "port" in d.root_cause.lower()
