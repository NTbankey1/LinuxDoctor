"""Shared pytest fixtures and configuration for all tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from linux_doctor.domain.models import (
    CommandRecommendation,
    Diagnosis,
    Evidence,
    Session,
)
from linux_doctor.infrastructure.kb_loader import (
    DomainKnowledgeBase,
    KnowledgeBaseLoader,
)

# ── Fixtures: Session ──────────────────────────────────────────

@pytest.fixture
def empty_session() -> Session:
    """A fresh session with no query set."""
    return Session()


@pytest.fixture
def docker_session() -> Session:
    """A session primed with a Docker query."""
    return Session(user_query="docker permission denied")


@pytest.fixture
def nginx_session() -> Session:
    return Session(user_query="nginx failed to start")


@pytest.fixture
def ssh_session() -> Session:
    return Session(user_query="ssh connection refused")


# ── Fixtures: Evidence ──────────────────────────────────────────

@pytest.fixture
def mock_evidence_success() -> Evidence:
    return Evidence(
        command_run="groups",
        stdout="ntbankey sudo",
        stderr="",
        return_code=0,
    )


@pytest.fixture
def mock_evidence_failure() -> Evidence:
    return Evidence(
        command_run="ls -l /var/run/docker.sock",
        stdout="",
        stderr="ls: cannot access: Permission denied",
        return_code=2,
    )


# ── Fixtures: Knowledge Base ──────────────────────────────────

@pytest.fixture(scope="session")
def kb_path() -> Path:
    return Path("data/kb")


@pytest.fixture(scope="session")
def kb_loader() -> KnowledgeBaseLoader:
    return KnowledgeBaseLoader("data/kb")


@pytest.fixture(scope="session")
def docker_kb(kb_loader) -> DomainKnowledgeBase:
    kb = kb_loader.load_domain("docker")
    assert kb is not None, "docker.yaml KB must exist"
    return kb


@pytest.fixture(scope="session")
def nginx_kb(kb_loader) -> DomainKnowledgeBase:
    kb = kb_loader.load_domain("nginx")
    assert kb is not None, "nginx.yaml KB must exist"
    return kb


@pytest.fixture(scope="session")
def ssh_kb(kb_loader) -> DomainKnowledgeBase:
    kb = kb_loader.load_domain("ssh")
    assert kb is not None, "ssh.yaml KB must exist"
    return kb


# ── Fixtures: Mock Executor ────────────────────────────────────

@pytest.fixture
def mock_executor():
    """A ShellExecutor that returns empty results."""
    executor = MagicMock()
    executor.execute.return_value = Evidence(
        command_run="mock", stdout="", stderr="", return_code=0,
    )
    return executor


# ── Fixtures: Database ─────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    from linux_doctor.infrastructure.database.repository import SessionRepository
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    repo = SessionRepository(db_path)
    yield repo
    Path(db_path).unlink(missing_ok=True)


# ── Fixtures: ML Model ─────────────────────────────────────────

@pytest.fixture(scope="session")
def trained_predictor():
    """Load the trained ML predictor (must exist)."""
    from linux_doctor.ml.predictor import IssueClassifier
    return IssueClassifier()


# ── Fixtures: Diagnosis ────────────────────────────────────────

@pytest.fixture
def sample_diagnosis() -> Diagnosis:
    return Diagnosis(
        category="nginx",
        root_cause="Port 80 occupied by apache2",
        confidence=0.95,
        recommended_fixes=[
            CommandRecommendation(
                command="systemctl stop apache2",
                explanation="Stop Apache",
                risk="moderate",
                is_safe_to_auto_run=False,
            ),
        ],
        explanation="Diagnosis from test",
        is_conclusive=True,
        margin=0.65,
    )
