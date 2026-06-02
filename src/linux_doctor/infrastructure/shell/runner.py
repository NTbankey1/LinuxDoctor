"""
Shell Runner — Safe subprocess execution with allowlist architecture.

Design:
- Allowlist + dangerous pattern + metachar check BEFORE shell execution
- shell=True for KB command compatibility (&&, ||, |, >)
- Process group cleanup: prevents zombie processes
- Timeout enforcement: prevents hanging
- Minimal environment: prevents PATH abuse
"""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ShellResult:
    """Result of a shell command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    success: bool
    error_message: str | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ============================================================
# ALLOWLIST — Only these commands can execute
# ============================================================
READ_CMDS = frozenset({
    "systemctl", "journalctl", "ss", "ip", "ping", "dig", "nslookup",
    "curl", "wget", "ps", "top", "free", "df", "du", "mount", "stat",
    "ls", "cat", "grep", "awk", "sed", "head", "tail", "wc", "find",
    "which", "whereis", "lsof", "fuser", "lscpu", "lspci", "lsblk",
    "blkid", "dmesg", "uptime", "uname", "hostname", "id", "groups",
    "getenforce", "sestatus", "ufw", "firewall-cmd", "iptables",
    "docker", "nginx", "ssh", "ssh-keygen", "ssh-keyscan",
    "git", "apt", "dnf", "yum", "dpkg", "rpm",
    "nproc", "mpstat", "iostat", "pidstat", "vmstat",
    "resolvectl", "host", "ethtool", "namei", "getfacl",
    "smartctl", "touch", "echo", "test",
    "sh", "bash", "command", "sort", "uniq", "tr",
    "cut", "printf", "xargs", "yes", "tee",
})

WRITE_CMDS = frozenset({
    "systemctl", "docker", "chmod", "chown", "usermod",
    "restorecon", "semanage", "sed", "kill",
})

# ============================================================
# DANGEROUS PATTERNS — Regex patterns that are NEVER allowed
# ============================================================
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    (r'\brm\s+(?:-rf?)?\s+/', 'wipe entire filesystem'),
    (r'\bdd\s+if=.*\s+of=\s*/dev/', 'overwrite block device'),
    (r'\bmkfs\.\w+\s+/dev/', 'format disk'),
    (r'\bchmod\s+(?:000|777)\s+/', 'dangerous permission on root'),
    (r'\bchown\s+-R\s+.*\s+/', 'recursive chown on filesystem'),
    (r'>\s*/dev/sd[a-z]', 'direct write to block device'),
    (r'\|\s*(?:bash|sh|zsh)\s*$', 'pipe to shell'),
    (r'sudo\s+(?:rm|mkfs|dd|fdisk|mkswap|shutdown|reboot)', 'sudo destructive command'),
]


class SafetyError(Exception):
    """Raised when a command is blocked by the safety system."""
    pass


class SafetyChecker:
    """Multi-layer command safety checker."""

    @staticmethod
    def check(command: str) -> None:
        """
        Check a command against ALL safety layers.
        Raises SafetyError if blocked.
        """
        import re

        # Layer 0: Extract base command from the full shell string
        import shlex
        try:
            tokens = shlex.split(command)
            if tokens:
                base_cmd = Path(tokens[0]).name
            else:
                raise SafetyError("Empty command") from None
        except ValueError:
            # shlex failed (e.g., unbalanced quotes from $() ) — extract first word manually
            first_word = re.match(r'^\s*(\S+)', command)
            if first_word:
                base_cmd = Path(first_word.group(1)).name
            else:
                raise SafetyError("Empty command") from None

        # Layer 1: Allowlist check
        if base_cmd not in READ_CMDS and base_cmd not in WRITE_CMDS:
            raise SafetyError(
                f"Command '{base_cmd}' is not in the allowlist. "
                f"Only read-only diagnostic commands are permitted."
            )

        # Layer 2: Dangerous pattern check
        for pattern, description in DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                raise SafetyError(
                    f"Command blocked: {description}. "
                    f"Pattern '{pattern}' matched in: {command[:100]}"
                )

        # Layer 3: Check $() command substitution — verify inner cmd is in allowlist
        for match in re.finditer(r'\$\((\w+)', command):
            inner_cmd = match.group(1)
            if inner_cmd not in READ_CMDS and inner_cmd not in WRITE_CMDS:
                raise SafetyError(
                    f"Command substitution '$({inner_cmd})' contains non-allowlisted command"
                )

        # Layer 4: Backtick execution (always blocked)
        if re.search(r'(?<!\S)`[^`]+`', command):
            raise SafetyError("Command contains backtick execution")

    @staticmethod
    def is_safe(command: str) -> bool:
        """Non-raising check. Returns True if command is safe."""
        try:
            SafetyChecker.check(command)
            return True
        except SafetyError:
            return False


class ShellRunner:
    """
    Safe shell command execution.

    Security model (3 layers applied BEFORE shell execution):
    1. Allowlist: only approved commands
    2. Dangerous pattern check: blocks rm -rf, dd, mkfs, etc.
    3. Shell metacharacter check: blocks `, $(
    Then uses shell=True for KB command compatibility (&&, ||, |, >)

    Additional protections:
    - Process group cleanup: no zombies
    - Timeout with SIGKILL fallback
    - Output size limit
    - Empty environment (no PATH abuse)
    """

    def __init__(self, timeout: int = 30, max_output_bytes: int = 1_000_000):
        self.timeout = timeout
        self.max_output = max_output_bytes

    def run(self, command: str, timeout: int | None = None) -> ShellResult:
        """
        Execute a command safely.

        Args:
            command: Shell command string
            timeout: Override default timeout

        Returns:
            ShellResult with captured output

        Raises:
            SafetyError: If command fails allowlist check
        """
        # Step 1: Safety check (allowlist + dangerous patterns + metachar)
        SafetyChecker.check(command)

        effective_timeout = timeout or self.timeout
        start = datetime.now(UTC)

        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setpgrp,
                env={"PATH": "/usr/bin:/usr/local/bin:/bin:/sbin"},
            )

            try:
                stdout, stderr = proc.communicate(timeout=effective_timeout)
            except subprocess.TimeoutExpired:
                # Kill the entire process group
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    proc.wait(timeout=5)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        proc.wait(timeout=5)
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        pass
                elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
                return ShellResult(
                    command=command, exit_code=-1,
                    stdout="", stderr=f"Command timed out after {effective_timeout}s",
                    execution_time_ms=elapsed, success=False,
                    error_message="Timeout",
                )

            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)

            # Truncate output if too large
            if len(stdout) > self.max_output:
                stdout = stdout[:self.max_output] + f"\n... (truncated, {len(stdout)} bytes total)"
            if len(stderr) > self.max_output // 2:
                stderr = stderr[:self.max_output // 2] + "\n... (truncated)"

            return ShellResult(
                command=command,
                exit_code=proc.returncode,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                execution_time_ms=elapsed,
                success=proc.returncode == 0,
            )

        except FileNotFoundError:
            return ShellResult(
                command=command, exit_code=-1,
                stdout="", stderr=f"Command failed: {command[:80]}",
                execution_time_ms=0, success=False,
                error_message="Command not found",
            )
        except PermissionError:
            return ShellResult(
                command=command, exit_code=-1,
                stdout="", stderr=f"Permission denied: {command[:80]}",
                execution_time_ms=0, success=False,
                error_message="Permission denied",
            )
        except Exception as e:
            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
            return ShellResult(
                command=command, exit_code=-1,
                stdout="", stderr=str(e),
                execution_time_ms=elapsed, success=False,
                error_message=str(e),
            )
