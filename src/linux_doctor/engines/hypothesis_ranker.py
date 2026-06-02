"""
Hypothesis Ranker — Bayesian confidence scoring for multi-hypothesis RCA.

Implements:
1. Bayesian belief update (posterior from prior + evidence likelihood)
2. Hypothesis-specific evidence weighting (support/contradict/neutral)
3. Deterministic elimination rules (contradiction = 0.0)
4. Confidence margin threshold (>20% required for conclusive)
5. Weighted ranking when margin is insufficient (return top N with scores)

Formulas:
    P(Cause | Evidence)     = P(Evidence | Cause) × P(Cause) / P(Evidence)
    P(Evidence)             = P(E | C) × P(C) + P(E | ~C) × (1 - P(C))
    Confidence margin        = P(top) - P(second)
    Margin threshold         = 0.20
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoredHypothesis:
    """A hypothesis with its current confidence score and evaluation state."""

    hypothesis_id: str
    description: str
    domain: str
    prior_confidence: float
    posterior_confidence: float
    status: str  # "pending" | "active" | "confirmed" | "eliminated" | "inconclusive"
    supporting_facts: list[str] = field(default_factory=list)
    contradicting_facts: list[str] = field(default_factory=list)
    eliminated_by: str | None = None
    confirmed_by: str | None = None

    @property
    def is_eliminated(self) -> bool:
        return self.status == "eliminated"

    @property
    def is_confirmed(self) -> bool:
        return self.status == "confirmed"

    @property
    def is_active(self) -> bool:
        return self.status in ("active", "pending")


@dataclass
class RankedDiagnosis:
    """Output of the hypothesis ranking process."""

    root_cause_id: str | None
    root_cause_desc: str | None
    confidence: float
    all_hypotheses: list[ScoredHypothesis]
    margin: float
    is_conclusive: bool
    diagnosis_summary: str


class HypothesisRanker:
    """
    Ranks competing hypotheses using Bayesian reasoning.

    Each hypothesis has an evidence-support map that determines whether
    each collected fact supports, contradicts, or is neutral. This
    prevents unrelated evidence from inflating hypothesis scores.
    """

    MARGIN_THRESHOLD = 0.20

    def __init__(self):
        pass

    def evaluate_hypotheses(
        self,
        hypotheses: list[dict[str, Any]],
        facts: dict[str, str],
        domain: str,
    ) -> RankedDiagnosis:
        """
        Evaluate all hypotheses against collected facts.

        Args:
            hypotheses: List of hypothesis dicts from KB rules
            facts: Dict of fact_key -> extracted value from evidence
            domain: Domain name for context

        Returns:
            RankedDiagnosis with scored hypotheses and root cause selection
        """
        scored: list[ScoredHypothesis] = []

        for hyp in hypotheses:
            hypothesis_id = hyp.get("id", "unknown")
            prior = hyp.get("confidence", 0.5)
            description = hyp.get("description", "")

            status, posterior, supporting, contradicting = (
                self._evaluate_single_hypothesis(hypothesis_id, prior, facts)
            )

            scored.append(ScoredHypothesis(
                hypothesis_id=hypothesis_id,
                description=description,
                domain=domain,
                prior_confidence=prior,
                posterior_confidence=posterior,
                status=status,
                supporting_facts=supporting,
                contradicting_facts=contradicting,
                eliminated_by=contradicting[0] if status == "eliminated" and contradicting else None,
            ))

        return self._rank_and_select(scored)

    def _evaluate_single_hypothesis(
        self,
        hypothesis_id: str,
        prior: float,
        facts: dict[str, str],
    ) -> tuple[str, float, list[str], list[str]]:
        """
        Evaluate a single hypothesis against facts using hypothesis-specific
        evidence weighting.

        Uses an evidence-support map to determine which facts support or
        contradict each hypothesis. This prevents unrelated evidence from
        biasing the score.

        Returns:
            (status, posterior_confidence, supporting_facts, contradicting_facts)
        """
        supporting: list[str] = []
        contradicting: list[str] = []

        # Step 1: Check deterministic elimination rules
        elimination_rules = self._get_elimination_rules()
        if hypothesis_id in elimination_rules:
            rule = elimination_rules[hypothesis_id]
            elimination_fact = rule.get("eliminate_if_matches")

            if elimination_fact:
                ev_value = facts.get(elimination_fact["key"], "")
                if self._check_condition(ev_value, elimination_fact):
                    contradicting.append(elimination_fact["key"])
                    return ("eliminated", 0.0, supporting, contradicting)

        # Step 2: Hypothesis-specific Bayesian update
        posterior = self._hypothesis_specific_update(hypothesis_id, prior, facts, supporting, contradicting)

        # Step 3: Determine status
        if posterior >= 0.90 and len(contradicting) == 0:
            return ("confirmed", posterior, supporting, contradicting)
        elif posterior > 0.0:
            return ("active", posterior, supporting, contradicting)
        else:
            return ("eliminated", 0.0, supporting, contradicting)

    def _hypothesis_specific_update(
        self,
        hypothesis_id: str,
        prior: float,
        facts: dict[str, str],
        supporting: list[str],
        contradicting: list[str],
    ) -> float:
        """
        Bayesian update with per-fact evidence weighting.

        Each hypothesis has an evidence-support map that assigns:
        - Supporting facts: likelihood = 0.85 (boosts posterior)
        - Contradicting facts: likelihood = 0.10 (reduces posterior)
        - Neutral facts: likelihood = 0.50 (no meaningful effect)
        - Empty/unknown facts: ignored
        """
        evidence_map = self._get_evidence_support_map()
        hyp_map = evidence_map.get(hypothesis_id, {})

        posterior = prior
        evidence_count = 0

        for fact_key, fact_value in facts.items():
            # Check if this fact has a known rule in the support map
            has_known_rule = fact_key in hyp_map

            # Skip empty values UNLESS a known rule explicitly handles emptiness
            if not fact_value or not fact_value.strip():
                if has_known_rule:
                    # A known rule exists — evaluate even if empty (e.g., is_empty operator)
                    pass
                else:
                    continue

            evidence_count += 1

            if fact_key in hyp_map:
                rule = hyp_map[fact_key]
                match_type = rule.get("match", "supports")
                operator = rule.get("operator", "is_not_empty")
                expected = rule.get("value", "")

                is_match = self._check_condition(
                    fact_value,
                    {"operator": operator, "value": expected},
                )

                if match_type == "supports" and is_match:
                    supporting.append(fact_key)
                    likelihood = 0.85
                elif match_type == "contradicts" and is_match:
                    contradicting.append(fact_key)
                    likelihood = 0.10
                elif match_type == "contradicts" and not is_match:
                    # Expected contradiction NOT found → evidence is neutral
                    likelihood = 0.15
                else:
                    likelihood = 0.50
            else:
                # Fact not in support map: irrelevant to this hypothesis
                # Use likelihood = false_positive to keep posterior unchanged
                likelihood = 0.15

            false_positive = 0.15
            p_not_cause = 1.0 - posterior
            p_evidence = (likelihood * posterior) + (false_positive * p_not_cause)
            if p_evidence > 0:
                posterior = (likelihood * posterior) / p_evidence

        if evidence_count == 0:
            return round(prior * 0.5, 4)

        return round(posterior, 4)

    def _check_condition(self, fact_value: str, condition: dict) -> bool:
        """Check a fact value against a condition."""
        operator = condition.get("operator", "is_not_empty")
        value = condition.get("value", "")

        match operator:
            case "is_not_empty":
                return bool(fact_value and fact_value.strip())
            case "is_empty":
                return not fact_value or not fact_value.strip()
            case "equals":
                return fact_value.strip() == value.strip()
            case "not_equals":
                return fact_value.strip() != value.strip()
            case "contains":
                return value.lower() in fact_value.lower()
            case "not_contains":
                return value.lower() not in fact_value.lower()
            case _:
                return False

    def _rank_and_select(self, scored: list[ScoredHypothesis]) -> RankedDiagnosis:
        """
        Select root cause from scored hypotheses.

        Rules:
        1. Confirmed hypotheses rank first (by posterior)
        2. Active hypotheses rank second (by posterior)
        3. Eliminated hypotheses excluded
        4. Root cause requires >20% margin over runner-up
        """
        confirmed = sorted(
            [h for h in scored if h.is_confirmed],
            key=lambda h: -h.posterior_confidence,
        )
        active = sorted(
            [h for h in scored if h.is_active],
            key=lambda h: -h.posterior_confidence,
        )

        candidate_pool = confirmed + active

        if not candidate_pool:
            return RankedDiagnosis(
                root_cause_id=None,
                root_cause_desc=None,
                confidence=0.0,
                all_hypotheses=scored,
                margin=0.0,
                is_conclusive=False,
                diagnosis_summary="No active hypotheses. All possible causes were eliminated by evidence.",
            )

        winner = candidate_pool[0]
        if len(candidate_pool) > 1:
            runner_up = candidate_pool[1]
            margin = winner.posterior_confidence - runner_up.posterior_confidence
        else:
            margin = winner.posterior_confidence

        if margin >= self.MARGIN_THRESHOLD or len(candidate_pool) == 1:
            return RankedDiagnosis(
                root_cause_id=winner.hypothesis_id,
                root_cause_desc=winner.description,
                confidence=winner.posterior_confidence,
                all_hypotheses=scored,
                margin=margin,
                is_conclusive=True,
                diagnosis_summary=(
                    f"Root cause identified: {winner.description} "
                    f"(confidence: {winner.posterior_confidence:.0%}, "
                    f"margin: {margin:.0%})"
                ),
            )
        else:
            return RankedDiagnosis(
                root_cause_id=None,
                root_cause_desc=f"Multiple possible causes (top: {winner.description})",
                confidence=winner.posterior_confidence,
                all_hypotheses=scored,
                margin=margin,
                is_conclusive=False,
                diagnosis_summary=(
                    f"Insufficient margin ({margin:.0%}) between top hypotheses. "
                    f"Top: {winner.description} ({winner.posterior_confidence:.0%}), "
                    f"Runner-up: {runner_up.description} ({runner_up.posterior_confidence:.0%})."
                ),
            )

    def format_ranking_table(self, scored: list[ScoredHypothesis]) -> list[dict]:
        """Format scored hypotheses for CLI display."""
        rows = []
        for h in sorted(scored, key=lambda x: -x.posterior_confidence):
            status_icon = {
                "confirmed": "✅",
                "active": "🔍",
                "eliminated": "❌",
                "pending": "⏳",
                "inconclusive": "❓",
            }.get(h.status, "•")
            rows.append({
                "id": h.hypothesis_id,
                "description": h.description,
                "confidence": f"{h.posterior_confidence:.0%}",
                "status": f"{status_icon} {h.status}",
            })
        return rows

    # ------------------------------------------------------------------
    # EVIDENCE-TO-HYPOTHESIS SUPPORT MAPS
    # Each hypothesis maps fact_keys to their support/contradict effect.
    # ------------------------------------------------------------------

    @staticmethod
    def _get_evidence_support_map() -> dict[str, dict[str, dict]]:
        """Map each hypothesis to which facts support or contradict it."""
        return {
            # SSH: sshd_not_running is supported by inactive sshd, NOT_LISTENING port
            "sshd_not_running": {
                "sshd_status": {"match": "supports", "operator": "not_equals", "value": "active"},
                "port_22_listening": {"match": "supports", "operator": "contains", "value": "NOT_LISTENING"},
            },
            # SSH: firewall_blocking_22 is supported by active firewall DROP rules,
            # but CONTRADICTED when firewall_ssh is empty (no blocking found)
            "firewall_blocking_22": {
                "firewall_ssh": {"match": "contradicts", "operator": "is_empty", "value": ""},
                "sshd_status": {"match": "contradicts", "operator": "equals", "value": "active"},
            },
            # Docker: user_not_in_docker_group
            "user_not_in_docker_group": {
                "user_groups": {"match": "supports", "operator": "not_contains", "value": "docker"},
            },
            "docker_socket_wrong_perms": {
                "socket_info": {"match": "supports", "operator": "is_empty", "value": ""},
            },
            # Port conflict hypotheses
            "port_conflict_80": {
                "port_80_owner": {"match": "supports", "operator": "is_not_empty", "value": ""},
            },
            "port_conflict_443": {
                "port_443_owner": {"match": "supports", "operator": "is_not_empty", "value": ""},
            },
            # Docker: docker_service_stopped
            "docker_service_stopped": {
                "docker_daemon_status": {"match": "contradicts", "operator": "equals", "value": "active"},
            },
            # Docker: container_crash_loop
            "container_crash_loop": {
                "container_state": {"match": "supports", "operator": "is_not_empty", "value": ""},
                "container_logs": {"match": "supports", "operator": "is_not_empty", "value": ""},
            },
            # Docker: container_oom_killed
            "container_oom_killed": {
                "container_state": {"match": "supports", "operator": "contains", "value": "oom"},
            },
            # Docker: docker_daemon_crashed
            "docker_daemon_crashed": {
                "docker_daemon_logs": {"match": "supports", "operator": "is_not_empty", "value": ""},
                "docker_daemon_status": {"match": "contradicts", "operator": "equals", "value": "active"},
                "docker_socket_exists": {"match": "contradicts", "operator": "not_equals", "value": "SOCKET_MISSING"},
            },
            # Docker: dangling_images
            "dangling_images": {
                "dangling_image_count": {"match": "supports", "operator": "greater_than", "value": "10"},
            },
            # Docker: docker_disk_full
            "docker_disk_full": {
                "docker_disk_use_percent": {"match": "supports", "operator": "greater_than", "value": "90"},
            },
        }

    @staticmethod
    def _get_elimination_rules() -> dict[str, dict]:
        """Return deterministic elimination rules: which facts eliminate which hypotheses."""
        return {
            "sshd_not_running": {
                "eliminate_if_matches": {"key": "sshd_status", "operator": "equals", "value": "active"},
            },
            "user_not_in_docker_group": {
                "eliminate_if_matches": {"key": "user_groups", "operator": "contains", "value": "docker"},
            },
            "port_conflict_80": {
                "eliminate_if_matches": {"key": "nginx_installed", "operator": "contains", "value": "NGINX_NOT_INSTALLED"},
            },
            "port_conflict_443": {
                "eliminate_if_matches": {"key": "nginx_installed", "operator": "contains", "value": "NGINX_NOT_INSTALLED"},
            },
            "nginx_not_installed": {
                "eliminate_if_matches": {"key": "nginx_installed", "operator": "contains", "value": "NGINX_BINARY_EXISTS"},
            },
            "docker_service_stopped": {
                "eliminate_if_matches": {"key": "docker_daemon_status", "operator": "equals", "value": "active"},
            },
            "docker_daemon_crashed": {
                "eliminate_if_matches": {"key": "docker_daemon_status", "operator": "equals", "value": "active"},
            },
        }
