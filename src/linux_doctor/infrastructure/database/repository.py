"""
SQLite Repository — Session persistence and audit trail.

Provides CRUD operations for all domain objects.
Uses WAL mode for concurrent read performance.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from linux_doctor.domain.models import (
    CommandRecommendation,
    Diagnosis,
    Evidence,
    Hypothesis,
    Session,
)

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,
    query           TEXT NOT NULL,
    domain          TEXT,
    domain_confidence REAL,
    intent          TEXT,
    status          TEXT NOT NULL DEFAULT 'active',
    error_message   TEXT,
    duration_ms     INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS symptoms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    symptom_id      TEXT NOT NULL,
    description     TEXT,
    match_score     REAL,
    matched_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    evidence_id     TEXT NOT NULL,
    command         TEXT NOT NULL,
    exit_code       INTEGER,
    stdout          TEXT,
    stderr          TEXT,
    parsed_output   TEXT,
    raw_output      TEXT,
    execution_ms    INTEGER,
    parse_success   INTEGER DEFAULT 0,
    error_message   TEXT,
    collected_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    hypothesis_id   TEXT NOT NULL,
    description     TEXT,
    prior_score     REAL DEFAULT 0.0,
    posterior_score REAL DEFAULT 0.0,
    status          TEXT NOT NULL DEFAULT 'pending',
    eliminated_by   TEXT,
    confirmed_by    TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    root_cause_id   TEXT,
    root_cause_desc TEXT,
    confidence      REAL,
    is_conclusive   INTEGER DEFAULT 0,
    margin          REAL,
    summary         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    diagnosis_id    INTEGER NOT NULL REFERENCES diagnoses(id) ON DELETE CASCADE,
    recommendation_id TEXT NOT NULL,
    command         TEXT NOT NULL,
    explanation     TEXT,
    risk            TEXT NOT NULL,
    is_applied      INTEGER DEFAULT 0,
    applied_at      TEXT,
    success         INTEGER,
    user_feedback   INTEGER
);

CREATE TABLE IF NOT EXISTS rule_firings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    rule_id         TEXT NOT NULL,
    iteration       INTEGER NOT NULL,
    condition_results TEXT,
    action_results  TEXT,
    fired_at        TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS incident_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash      TEXT NOT NULL UNIQUE,
    query_text      TEXT NOT NULL,
    domain          TEXT NOT NULL,
    root_cause_id   TEXT,
    root_cause_desc TEXT,
    confidence      REAL,
    frequency       INTEGER DEFAULT 1,
    last_seen       TEXT DEFAULT (datetime('now')),
    first_seen      TEXT DEFAULT (datetime('now')),
    resolution_success INTEGER DEFAULT 0,
    feedback_score  REAL
);

CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_domain ON sessions(domain);
CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence(session_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_session ON hypotheses(session_id);
CREATE INDEX IF NOT EXISTS idx_incident_hash ON incident_cache(query_hash);
"""


class SessionRepository:
    """Data access layer for all session data."""

    def __init__(self, db_path: str = "data/linux_doctor.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA_SQL)

    # --- SESSIONS ---

    def create_session(self, query: str, domain: str | None = None) -> Session:
        session = Session(session_id=str(uuid.uuid4()), user_query=query, domain=domain)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, query, domain, status) VALUES (?, ?, ?, 'active')",
                (session.session_id, query, domain),
            )
        return session

    def get_session(self, session_id: str) -> Session | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if row:
                return Session(session_id=row["id"], user_query=row["query"],
                               domain=row["domain"], status=row["status"])
            return None

    def update_session(self, session_id: str, **kwargs) -> None:
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [session_id]
        with self._get_conn() as conn:
            conn.execute(f"UPDATE sessions SET {fields} WHERE id = ?", values)

    def list_sessions(self, limit: int = 20) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, query, domain, status, created_at, duration_ms "
                "FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- EVIDENCE ---

    def save_evidence(self, session_id: str, evidence: Evidence) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO evidence
                   (session_id, evidence_id, command, exit_code, stdout, stderr,
                    parsed_output, raw_output, execution_ms, parse_success, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, evidence.command_run, evidence.command_run,
                 evidence.return_code, evidence.stdout, evidence.stderr,
                 json.dumps(evidence.parsed_output) if evidence.parsed_output else None,
                 evidence.stdout + "\n" + evidence.stderr,
                 evidence.execution_time_ms, 1 if evidence.is_success else 0, None),
            )
            return cur.lastrowid

    def get_session_evidence(self, session_id: str) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence WHERE session_id = ? ORDER BY collected_at",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- HYPOTHESES ---

    def save_hypothesis(self, session_id: str, hypothesis: Hypothesis) -> None:
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM hypotheses WHERE session_id = ? AND hypothesis_id = ?",
                (session_id, hypothesis.id),
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE hypotheses SET posterior_score = ?, status = ?,
                           eliminated_by = ?, updated_at = datetime('now')
                       WHERE id = ?""",
                    (hypothesis.confidence_score, hypothesis.status.value,
                     hypothesis.eliminated_by, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO hypotheses
                       (session_id, hypothesis_id, description, prior_score,
                        posterior_score, status)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (session_id, hypothesis.id, hypothesis.description,
                     hypothesis.prior_score, hypothesis.confidence_score,
                     hypothesis.status.value),
                )

    def get_session_hypotheses(self, session_id: str) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM hypotheses WHERE session_id = ? ORDER BY posterior_score DESC",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- DIAGNOSES ---

    def save_diagnosis(self, session_id: str, diagnosis: Diagnosis) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT OR REPLACE INTO diagnoses
                   (session_id, root_cause_id, root_cause_desc, confidence,
                    is_conclusive, margin, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, diagnosis.root_cause, diagnosis.root_cause,
                 diagnosis.confidence, 1 if diagnosis.is_conclusive else 0,
                 diagnosis.margin, diagnosis.explanation[:500]),
            )
            return cur.lastrowid

    def save_recommendations(self, diagnosis_id: int, fixes: list[CommandRecommendation]) -> None:
        with self._get_conn() as conn:
            for fix in fixes:
                conn.execute(
                    """INSERT INTO recommendations
                       (diagnosis_id, recommendation_id, command, explanation, risk)
                       VALUES (?, ?, ?, ?, ?)""",
                    (diagnosis_id, fix.command[:100], fix.command,
                     fix.explanation, fix.risk),
                )

    # --- INCIDENT CACHE ---

    def find_similar_incident(self, query: str, domain: str) -> dict | None:
        """Find a previously diagnosed incident with the same query+domain."""
        import hashlib
        query_hash = hashlib.sha256(f"{query}:{domain}".encode()).hexdigest()
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM incident_cache WHERE query_hash = ?", (query_hash,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE incident_cache SET frequency = frequency + 1, last_seen = datetime('now') WHERE id = ?",
                    (row["id"],),
                )
                return dict(row)
            return None

    def cache_incident(self, query: str, domain: str, root_cause_id: str,
                       root_cause_desc: str, confidence: float) -> None:
        import hashlib
        query_hash = hashlib.sha256(f"{query}:{domain}".encode()).hexdigest()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO incident_cache
                   (query_hash, query_text, domain, root_cause_id, root_cause_desc, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (query_hash, query, domain, root_cause_id, root_cause_desc, confidence),
            )
