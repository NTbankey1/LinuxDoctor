"""Shell execution — delegates to new allowlist-based ShellRunner."""

from __future__ import annotations

from linux_doctor.domain.models import Evidence
from linux_doctor.infrastructure.shell.runner import SafetyError, ShellRunner

UnsafeCommandError = SafetyError


class ShellExecutor:
    """Executes shell commands safely. Delegates to ShellRunner."""

    def __init__(self, timeout: int = 30):
        self._runner = ShellRunner(timeout=timeout)

    def execute(self, command: str) -> Evidence:
        """Execute a command and return Evidence."""
        result = self._runner.run(command)
        return Evidence(
            command_run=result.command,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.exit_code,
            execution_time_ms=result.execution_time_ms,
        )
