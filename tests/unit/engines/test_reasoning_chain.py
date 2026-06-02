"""Tests for the reasoning chain (audit trail)."""

from __future__ import annotations

from linux_doctor.engines.reasoning_chain import ReasoningChain, ReasoningStepType


class TestReasoningChain:
    def test_add_step(self):
        chain = ReasoningChain()
        sid = chain.add_step(ReasoningStepType.SYMPTOM_MATCHED, "test")
        assert sid == "step_0001"
        assert len(chain.get_chain()) == 1

    def test_sequential_ids(self):
        chain = ReasoningChain()
        sid1 = chain.add_step(ReasoningStepType.SYMPTOM_MATCHED, "first")
        sid2 = chain.add_step(ReasoningStepType.RULE_FIRED, "second")
        assert sid1 == "step_0001"
        assert sid2 == "step_0002"

    def test_step_with_data(self):
        chain = ReasoningChain()
        chain.add_step(
            ReasoningStepType.EVIDENCE_COLLECTED,
            "ran command",
            input_data={"command": "systemctl status"},
            output_data={"status": "inactive"},
            confidence=0.9,
        )
        steps = chain.get_chain()
        assert steps[0].output_data["status"] == "inactive"
        assert steps[0].confidence == 0.9

    def test_to_dict(self):
        chain = ReasoningChain()
        chain.add_step(ReasoningStepType.SYMPTOM_MATCHED, "test")
        d = chain.to_dict()
        assert len(d) == 1
        assert d[0]["type"] == "symptom_matched"

    def test_render_text(self):
        chain = ReasoningChain()
        chain.add_step(ReasoningStepType.SYMPTOM_MATCHED, "Test symptom")
        text = chain.render_text()
        assert "Test symptom" in text

    def test_format_for_explain(self):
        chain = ReasoningChain()
        chain.add_step(ReasoningStepType.SYMPTOM_MATCHED, "connection refused")
        chain.add_step(ReasoningStepType.ROOT_CAUSE_SELECTED, "SSHD not running")
        out = chain.format_for_explain()
        assert "connection refused" in out
        assert "SSHD not running" in out

    def test_root_cause_not_found(self):
        chain = ReasoningChain()
        assert chain.root_cause_step is None
        assert chain.confidence == 0.0

    def test_root_cause_found(self):
        chain = ReasoningChain()
        chain.add_step(ReasoningStepType.ROOT_CAUSE_SELECTED, "cause", confidence=0.85)
        assert chain.root_cause_step is not None
        assert chain.confidence == 0.85

    def test_recommendations(self):
        chain = ReasoningChain()
        chain.add_step(ReasoningStepType.RECOMMENDATION_GENERATED, "fix",
                       output_data={"command": "systemctl restart"})
        recs = chain.get_recommendations()
        assert len(recs) == 1
        assert recs[0]["command"] == "systemctl restart"
