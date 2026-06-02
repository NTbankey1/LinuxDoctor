"""Tests for the ShellRunner safety system."""

from __future__ import annotations

import pytest

from linux_doctor.infrastructure.shell.runner import (
    DANGEROUS_PATTERNS,
    SafetyChecker,
    SafetyError,
    ShellRunner,
)


class TestSafetyChecker:
    def test_read_commands_allowed(self):
        safe = [
            "systemctl status nginx",
            "journalctl -u docker -n 20",
            "ss -tulpn",
            "ip link show",
            "df -h /",
            "free -m",
            "ls -la /var/log/",
        ]
        for cmd in safe:
            assert SafetyChecker.is_safe(cmd), f"Should be safe: {cmd}"

    def test_unknown_commands_blocked(self):
        blocked = [
            "python3 -c 'import os'",
            "perl -e 'system(\"reboot\")'",
            "ruby -e 'exec(\"shutdown\")'",
        ]
        for cmd in blocked:
            assert not SafetyChecker.is_safe(cmd), f"Should be blocked: {cmd}"

    def test_dangerous_patterns_blocked(self):
        dangerous = [
            ("rm -rf /var/log", "rm -rf"),
            ("rm -rf /", "rm root"),
            ("dd if=/dev/zero of=/dev/sda", "dd overwrite"),
            ("mkfs.ext4 /dev/sda1", "mkfs"),
            ("chmod 000 /etc", "chmod 000"),
            ("sudo rm -rf /", "sudo + rm"),
        ]
        for cmd, desc in dangerous:
            assert not SafetyChecker.is_safe(cmd), f"Should be blocked: {desc}"

    def test_safe_systemctl_allowed(self):
        safe = [
            "systemctl start nginx",
            "systemctl stop apache2",
            "systemctl restart docker",
            "systemctl enable --now sshd",
        ]
        for cmd in safe:
            assert SafetyChecker.is_safe(cmd), f"Should be safe: {cmd}"

    def test_empty_command_raises(self):
        with pytest.raises(SafetyError, match="Empty"):
            SafetyChecker.check("")

    def test_shell_metacharacters_blocked(self):
        with pytest.raises(SafetyError):
            SafetyChecker.check("echo `whoami`")
        with pytest.raises(SafetyError):
            SafetyChecker.check("echo $(whoami)")

    def test_all_dangerous_patterns_compile(self):
        import re
        for pattern, _desc in DANGEROUS_PATTERNS:
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern: {pattern}")

    def test_allowlist_has_command_keyword(self):
        assert SafetyChecker.is_safe("command -v nginx >/dev/null 2>&1 && echo EXISTS || echo NOT_FOUND")


class TestShellRunner:
    @pytest.fixture
    def runner(self):
        return ShellRunner(timeout=5)

    def test_simple_echo(self, runner):
        r = runner.run("echo 'hello world'")
        assert r.success
        assert "hello world" in r.stdout
        assert r.exit_code == 0

    def test_unsafe_command_blocked(self, runner):
        with pytest.raises(SafetyError):
            runner.run("rm -rf /")
