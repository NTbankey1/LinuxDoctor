"""Tests for the CLI application module."""

from __future__ import annotations

from linux_doctor.cli.app import _detect_domain, _keyword_route


class TestKeywordRouting:
    def test_docker_keyword(self):
        assert _keyword_route("docker permission denied") == "docker"

    def test_nginx_keyword(self):
        assert _keyword_route("nginx failed to start") == "nginx"

    def test_ssh_keyword(self):
        assert _keyword_route("ssh connection refused") == "ssh"

    def test_disk_keyword(self):
        assert _keyword_route("disk full no space") == "disk"

    def test_git_keyword(self):
        assert _keyword_route("git push rejected") == "git"

    def test_no_match(self):
        assert _keyword_route("weather report today") is None


class TestDomainDetection:
    """Requires trained ML model (best_model.pkl)."""

    def test_docker_detected(self):
        dom, conf, method = _detect_domain("docker permission denied")
        assert dom == "docker", f"Got {dom}"

    def test_nginx_detected(self):
        dom, conf, _method = _detect_domain("nginx failed to start")
        assert dom == "nginx", f"Got {dom}"

    def test_ssh_detected(self):
        dom, conf, _method = _detect_domain("ssh connection refused")
        assert dom == "ssh", f"Got {dom}"

    def test_disk_detected(self):
        dom, conf, _method = _detect_domain("disk full no space left")
        assert dom == "disk", f"Got {dom}"

    def test_git_detected(self):
        dom, conf, _method = _detect_domain("git push rejected")
        assert dom == "git", f"Got {dom}"

    def test_short_query_nginx(self):
        """Short query 'nginx' should still resolve to nginx."""
        dom, conf, _method = _detect_domain("nginx")
        assert dom == "nginx", f"Got {dom}"

    def test_short_query_docker(self):
        dom, conf, _method = _detect_domain("docker")
        assert dom == "docker", f"Got {dom}"
