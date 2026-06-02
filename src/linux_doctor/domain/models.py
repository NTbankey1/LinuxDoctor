"""Domain models for the Linux Doctor Expert System — Clean Architecture Core."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class HypothesisStatus(Enum):
    """Current state of a diagnostic hypothesis."""
    PENDING = "pending"
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    ELIMINATED = "eliminated"
    INCONCLUSIVE = "inconclusive"


@dataclass
class Fact:
    """A concrete piece of evidence about the system."""
    key: str
    value: Any
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 1.0


@dataclass
class Evidence:
    """Evidence collected to prove or disprove a hypothesis."""
    command_run: str
    stdout: str
    stderr: str
    return_code: int
    gathered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    parsed_output: dict | None = None
    execution_time_ms: int = 0

    @property
    def is_success(self) -> bool:
        return self.return_code == 0


@dataclass
class Hypothesis:
    """A potential root cause being investigated."""
    id: str
    description: str
    domain: str
    confidence_score: float = 0.0
    prior_score: float = 0.0
    status: HypothesisStatus = HypothesisStatus.PENDING
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    eliminated_by: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status in (HypothesisStatus.PENDING, HypothesisStatus.ACTIVE)

    @property
    def is_eliminated(self) -> bool:
        return self.status == HypothesisStatus.ELIMINATED

    @property
    def is_confirmed(self) -> bool:
        return self.status == HypothesisStatus.CONFIRMED


@dataclass
class CommandRecommendation:
    """A recommended command to fix or investigate an issue."""
    command: str
    explanation: str
    risk: str = "moderate"
    is_safe_to_auto_run: bool = False
    rollback_command: str | None = None


@dataclass
class Diagnosis:
    """The final conclusion reached by the system."""
    category: str
    root_cause: str
    confidence: float
    recommended_fixes: list[CommandRecommendation]
    explanation: str
    is_conclusive: bool = True
    margin: float = 0.0


@dataclass
class Session:
    """A troubleshooting session with full audit trail."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_query: str = ""
    domain: str | None = None
    domain_confidence: float = 0.0
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: str = "active"
    facts: list[Fact] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    diagnosis: Diagnosis | None = None
    reasoning_chain: Any = None
    duration_ms: int = 0
    error_message: str | None = None


# Re-export KBRule from kb_loader to keep the name accessible
from linux_doctor.infrastructure.kb_loader import KBRule as KBRule  # noqa: E402, F811
