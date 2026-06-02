"""
Reasoning Chain — Tracks the full diagnostic reasoning path.

Records every step from initial symptom through rule firings,
evidence collection, hypothesis generation, and final root cause.
Provides a serializable audit trail for explainability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ReasoningStepType(Enum):
    SYMPTOM_MATCHED = "symptom_matched"
    RULE_FIRED = "rule_fired"
    EVIDENCE_COLLECTED = "evidence_collected"
    FACT_PRODUCED = "fact_produced"
    HYPOTHESIS_GENERATED = "hypothesis_generated"
    HYPOTHESIS_ELIMINATED = "hypothesis_eliminated"
    HYPOTHESIS_CONFIRMED = "hypothesis_confirmed"
    HYPOTHESIS_RANKED = "hypothesis_ranked"
    ROOT_CAUSE_SELECTED = "root_cause_selected"
    RECOMMENDATION_GENERATED = "recommendation_generated"


@dataclass
class ReasoningStep:
    """A single step in the diagnostic reasoning chain."""

    step_id: str
    step_type: ReasoningStepType
    description: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    parent_step_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step_id,
            "type": self.step_type.value,
            "description": self.description,
            "input": self.input_data,
            "output": self.output_data,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class ReasoningChain:
    """
    Directed acyclic graph of diagnostic reasoning steps.

    Each step links to its parent, creating a traceable chain:
    Symptom → Rule → Evidence → Fact → Hypothesis → Root Cause → Fix

    Usage:
        chain = ReasoningChain()
        chain.add_step(ReasoningStep(...))
        chain.render()  # Returns formatted trace
    """

    def __init__(self):
        self.steps: list[ReasoningStep] = []
        self._step_counter: int = 0

    def add_step(
        self,
        step_type: ReasoningStepType,
        description: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        confidence: float = 0.0,
        parent_step_id: str | None = None,
    ) -> str:
        """Add a reasoning step and return its ID."""
        self._step_counter += 1
        step_id = f"step_{self._step_counter:04d}"
        step = ReasoningStep(
            step_id=step_id,
            step_type=step_type,
            description=description,
            input_data=input_data or {},
            output_data=output_data or {},
            confidence=confidence,
            parent_step_id=parent_step_id,
        )
        self.steps.append(step)
        return step_id

    def get_chain(self) -> list[ReasoningStep]:
        """Return steps in order."""
        return self.steps

    def render_text(self) -> str:
        """Render reasoning chain as a text tree."""
        lines = []
        for step in self.steps:
            indent = "  " * (1 if step.parent_step_id else 0)
            icon = self._icon_for_type(step.step_type)
            conf = f" ({step.confidence:.0%})" if step.confidence > 0 else ""
            lines.append(f"{indent}{icon} {step.description}{conf}")
            if step.output_data:
                for key, value in step.output_data.items():
                    if value:
                        lines.append(f"{indent}  └─ {key}: {value}")
        return "\n".join(lines)

    def to_dict(self) -> list[dict[str, Any]]:
        """Serialize entire chain to dict for CLI display."""
        return [step.to_dict() for step in self.steps]

    @staticmethod
    def _icon_for_type(step_type: ReasoningStepType) -> str:
        icons = {
            ReasoningStepType.SYMPTOM_MATCHED: "🔍",
            ReasoningStepType.RULE_FIRED: "⚡",
            ReasoningStepType.EVIDENCE_COLLECTED: "📡",
            ReasoningStepType.FACT_PRODUCED: "📌",
            ReasoningStepType.HYPOTHESIS_GENERATED: "🤔",
            ReasoningStepType.HYPOTHESIS_ELIMINATED: "❌",
            ReasoningStepType.HYPOTHESIS_CONFIRMED: "✅",
            ReasoningStepType.HYPOTHESIS_RANKED: "📊",
            ReasoningStepType.ROOT_CAUSE_SELECTED: "💡",
            ReasoningStepType.RECOMMENDATION_GENERATED: "🔧",
        }
        return icons.get(step_type, "•")

    @property
    def root_cause_step(self) -> ReasoningStep | None:
        """Return the root cause selection step if present."""
        for step in reversed(self.steps):
            if step.step_type == ReasoningStepType.ROOT_CAUSE_SELECTED:
                return step
        return None

    @property
    def confidence(self) -> float:
        """Return the final diagnosis confidence."""
        root = self.root_cause_step
        return root.confidence if root else 0.0

    def get_recommendations(self) -> list[dict[str, Any]]:
        """Return recommendations from the chain."""
        return [
            step.output_data
            for step in self.steps
            if step.step_type == ReasoningStepType.RECOMMENDATION_GENERATED
        ]

    def format_for_explain(self) -> str:
        """Format the chain for the 'linux-doctor explain' command."""
        lines = ["╔═══════════════════════════════════════════════╗",
                 "║         DIAGNOSTIC REASONING CHAIN           ║",
                 "╚═══════════════════════════════════════════════╝", ""]
        for step in self.steps:
            icon = self._icon_for_type(step.step_type)
            desc = step.description
            lines.append(f"  {icon}  {desc}")
            if step.output_data and any(v for v in step.output_data.values()):
                for key, val in step.output_data.items():
                    if val:
                        lines.append(f"      └─ {key}: {val}")
            lines.append("")
        return "\n".join(lines)
