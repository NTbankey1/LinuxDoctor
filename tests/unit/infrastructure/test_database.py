"""Tests for the SQLite database repository."""

from __future__ import annotations


class TestSessionRepository:
    def test_create_session(self, temp_db):
        s = temp_db.create_session("nginx failed to start", "nginx")
        assert s.session_id is not None
        assert s.user_query == "nginx failed to start"

    def test_get_session(self, temp_db):
        created = temp_db.create_session("test", "test")
        retrieved = temp_db.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.user_query == "test"

    def test_get_nonexistent_session(self, temp_db):
        assert temp_db.get_session("nonexistent") is None

    def test_list_sessions(self, temp_db):
        temp_db.create_session("q1", "nginx")
        temp_db.create_session("q2", "docker")
        temp_db.create_session("q3", "ssh")
        sessions = temp_db.list_sessions(limit=10)
        assert len(sessions) >= 3

    def test_list_sessions_empty(self):
        import tempfile
        from pathlib import Path

        from linux_doctor.infrastructure.database.repository import SessionRepository
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            repo = SessionRepository(f.name)
        assert len(repo.list_sessions()) == 0
        Path(f.name).unlink(missing_ok=True)

    def test_update_session(self, temp_db):
        s = temp_db.create_session("test", "test")
        temp_db.update_session(s.session_id, status="complete", duration_ms=1000)
        conn = temp_db._get_conn()
        row = conn.execute(
            "SELECT status FROM sessions WHERE id = ?", (s.session_id,)
        ).fetchone()
        conn.close()
        assert row["status"] == "complete"

    def test_save_diagnosis(self, temp_db, sample_diagnosis):
        s = temp_db.create_session("test", "nginx")
        diag_id = temp_db.save_diagnosis(s.session_id, sample_diagnosis)
        assert diag_id is not None

    def test_save_recommendations(self, temp_db, sample_diagnosis):
        s = temp_db.create_session("test", "nginx")
        diag_id = temp_db.save_diagnosis(s.session_id, sample_diagnosis)
        temp_db.save_recommendations(diag_id, sample_diagnosis.recommended_fixes)

    def test_incident_cache(self, temp_db):
        result = temp_db.find_similar_incident("nginx port 80", "nginx")
        assert result is None
        temp_db.cache_incident("nginx port 80", "nginx", "port_conflict", "Port occupied", 0.95)
        result = temp_db.find_similar_incident("nginx port 80", "nginx")
        assert result is not None
        assert result["root_cause_id"] == "port_conflict"

    def test_incident_frequency(self, temp_db):
        temp_db.cache_incident("test query", "test", "cause", "desc", 0.9)
        temp_db.find_similar_incident("test query", "test")
        temp_db.find_similar_incident("test query", "test")
        result = temp_db.find_similar_incident("test query", "test")
        assert result["frequency"] >= 3
