"""Tests for configuration settings."""

from __future__ import annotations

from linux_doctor.config.settings import Settings


class TestSettings:
    def test_default_values(self):
        s = Settings()
        assert s.debug is False
        assert s.log_level == "INFO"
        assert s.shell_timeout_seconds == 10

    def test_forbidden_commands(self):
        s = Settings()
        assert "sudo" in s.forbidden_commands
        assert "rm" in s.forbidden_commands

    def test_kb_path_default(self):
        s = Settings()
        assert s.kb_path == "data/kb"
