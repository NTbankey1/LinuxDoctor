"""Integration tests — full pipeline from symptom to diagnosis."""

from __future__ import annotations

from unittest.mock import MagicMock

from linux_doctor.domain.models import Session
from linux_doctor.engines.rule_engine import RuleEngine


class TestFullPipeline:
    """Test end-to-end flow: symptom → evidence → diagnosis."""

    def test_ssh_pipeline(self, ssh_kb):
        engine = RuleEngine(kb=ssh_kb)
        m = MagicMock()
        def se(cmd):
            if "is-active" in cmd:
                return MagicMock(stdout="inactive", stderr="", return_code=3)
            if "ss -tulpn" in cmd or "netstat" in cmd:
                return MagicMock(stdout="NOT_LISTENING", stderr="", return_code=1)
            if "iptables" in cmd or "ufw" in cmd or "firewall-cmd" in cmd:
                return MagicMock(stdout="FIREWALL_CHECK_FAILED", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = se
        engine.executor = m
        d = engine.diagnose(Session(user_query="ssh connection refused"))
        assert d is not None
        assert d.is_conclusive

    def test_docker_pipeline_user_not_in_group(self, docker_kb):
        engine = RuleEngine(kb=docker_kb)
        m = MagicMock()
        def se(cmd):
            if "groups" in cmd:
                return MagicMock(stdout="ntbankey sudo wheel", stderr="", return_code=0)
            if "docker.sock" in cmd:
                return MagicMock(stdout="srw-rw---- 1 root docker", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = se
        engine.executor = m
        d = engine.diagnose(Session(user_query="docker permission denied"))
        assert d is not None
        assert "group" in d.root_cause.lower()

    def test_nginx_pipeline_port_conflict(self, nginx_kb):
        engine = RuleEngine(kb=nginx_kb)
        m = MagicMock()
        def se(cmd):
            if ":80 " in cmd:
                return MagicMock(stdout='LISTEN users:(("apache2",pid=1234))', stderr="", return_code=0)
            if ":443 " in cmd:
                return MagicMock(stdout="", stderr="", return_code=0)
            if "nginx -t" in cmd:
                return MagicMock(stdout="syntax is ok", stderr="", return_code=0)
            if "status nginx" in cmd:
                return MagicMock(stdout="Active: failed", stderr="", return_code=3)
            if "command -v nginx" in cmd:
                return MagicMock(stdout="NGINX_BINARY_EXISTS", stderr="", return_code=0)
            if "rpm -q nginx" in cmd or "dpkg -l nginx" in cmd:
                return MagicMock(stdout="NGINX_PKG_INSTALLED", stderr="", return_code=0)
            if "systemctl list-unit-files nginx" in cmd:
                return MagicMock(stdout="NGINX_UNIT_EXISTS", stderr="", return_code=0)
            return MagicMock(stdout="", stderr="", return_code=0)
        m.execute.side_effect = se
        engine.executor = m
        d = engine.diagnose(Session(user_query="nginx failed to start"))
        assert d is not None
        assert d.root_cause is not None

    def test_domain_detection_accuracy(self, trained_predictor):
        """Test ML domain detection on key queries."""
        tests = [
            ("docker permission denied", "docker"),
            ("nginx failed to start", "nginx"),
            ("ssh connection refused", "ssh"),
            ("disk full no space left", "disk"),
            ("out of memory oom killer", "memory"),
            ("git push rejected", "git"),
            ("cpu load average high", "cpu"),
            ("network unreachable", "network"),
            ("dns resolution failed", "dns"),
            ("systemctl start failed", "systemd"),
        ]
        correct = 0
        for query, expected in tests:
            pred = trained_predictor.predict(query)
            if pred.domain == expected:
                correct += 1
        assert correct >= 8, f"Only {correct}/10 correct (need 8+)"

    def test_reasoning_chain_attached(self, ssh_kb):
        from unittest.mock import MagicMock, patch
        engine = RuleEngine(kb=ssh_kb)
        with patch.object(engine.executor, "execute") as m:
            m.return_value = MagicMock(stdout="inactive", stderr="", return_code=0)
            engine.diagnose(Session(user_query="ssh connection refused"))
        chain = engine.get_reasoning_chain()
        assert len(chain.get_chain()) > 0
