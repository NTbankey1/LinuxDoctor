"""
Forward Chaining Rule Engine — Multi-hop diagnostic engine.

Architecture:
    Symptom → Rule → Evidence → Fact → Rule → Fact → ... → Diagnosis

Key features:
    - Multi-hop forward chaining (facts trigger new rules)
    - Reasoning chain tracking (full audit trail)
    - Bayesian hypothesis scoring and ranking
    - Deterministic elimination (contradiction)
    - Max iteration guard (prevents infinite loops)
"""

from __future__ import annotations

import re
from typing import Any

from linux_doctor.domain.models import (
    CommandRecommendation,
    Diagnosis,
    Evidence,
    Session,
)
from linux_doctor.engines.hypothesis_ranker import HypothesisRanker
from linux_doctor.engines.reasoning_chain import ReasoningChain, ReasoningStepType
from linux_doctor.infrastructure.kb_loader import (
    DomainKnowledgeBase,
    KBRule,
    RcaCondition,
)
from linux_doctor.infrastructure.logger import log
from linux_doctor.infrastructure.shell_executor import ShellExecutor, UnsafeCommandError

# Common Linux service names for extraction from user queries
_COMMON_SERVICES = [
    "nginx", "apache2", "httpd", "mysql", "mariadb", "postgresql",
    "postgres", "redis", "memcached", "mongod", "elasticsearch",
    "ssh", "sshd", "docker", "containerd", "kubelet", "kubectl",
    "cron", "rsyslog", "systemd-journald", "NetworkManager",
    "ufw", "iptables", "named", "bind9", "unbound",
    "php-fpm", "gunicorn", "uwsgi", "celery", "rabbitmq-server",
    "prometheus", "grafana-server", "node_exporter", "alertmanager",
    "jenkins", "gitlab-runner", "nexus", "sonarqube",
]


class RuleEngine:
    """
    Multi-hop forward chaining rule engine.

    Each iteration:
    1. Match rules against current working memory (facts + symptoms)
    2. Select highest-priority fireable rule
    3. Execute rule (collect evidence, generate facts)
    4. New facts may trigger additional rules
    5. Repeat until no fireable rules or max iterations reached

    After the chain terminates:
    - All hypotheses are ranked and scored
    - Root cause selected by confidence margin
    - Reasoning chain provides full audit trail
    """

    MAX_ITERATIONS = 50

    def __init__(self, kb: DomainKnowledgeBase, executor: ShellExecutor | None = None) -> None:
        self.kb = kb
        self.executor = executor or ShellExecutor()
        self.ranker = HypothesisRanker()
        self.chain = ReasoningChain()
        self.facts: dict[str, str] = {}
        self.fired_rules: set[str] = set()
        self.generated_hypotheses: list[dict[str, Any]] = []

    @staticmethod
    def _resolve_template(text: str, facts: dict[str, str]) -> str:
        """Resolve {{key}}, {{key.subkey}}, and <placeholder> templates.

        {{key}}        — resolved from facts dict; missing keys keep original {{...}}
        {{key.subkey}} — flattened to facts.get(key, ...)
        <service>      — resolved from facts.get('service_name', '<service>')
        <high_io_pid>  — resolved from facts.get('high_io_pid', '<high_io_pid>')
        """
        def curly_replacer(match: re.Match) -> str:
            var_path = match.group(1)
            base_key = var_path.split(".")[0]
            return facts.get(base_key, match.group(0))

        def angle_replacer(match: re.Match) -> str:
            placeholder = match.group(1)
            # backward compat: <service> can also be served by service_name fact
            if placeholder == "service" and "service" not in facts and "service_name" in facts:
                return facts["service_name"]
            return facts.get(placeholder, match.group(0))

        result = re.sub(r'\{\{(\S+)\}\}', curly_replacer, text)
        result = re.sub(r'<(\w+)>', angle_replacer, result)
        return result

    # ------------------------------------------------------------------
    # PUBLIC API — Entry point for diagnosis
    # ------------------------------------------------------------------

    def diagnose(self, session: Session) -> Diagnosis | None:
        """Run multi-hop forward chaining diagnosis."""
        user_query = session.user_query
        log.info(f"\n[bold blue]Rule Engine:[/bold blue] '{user_query}'")

        # Extract service name from query early so templates can use it
        service_name = self._extract_service_name(user_query)
        if service_name:
            self.facts["service_name"] = service_name

        # Step 1: Match initial symptoms
        matched_rules = self._match_symptoms(user_query)
        if not matched_rules:
            log.warning("[yellow]No matching rules found for this query.[/yellow]")
            self.chain.add_step(
                ReasoningStepType.SYMPTOM_MATCHED,
                f"No symptoms matched for: '{user_query}'",
                confidence=0.0,
            )
            return None

        # Step 2: Multi-hop forward chaining loop
        self._forward_chain(matched_rules)

        # Step 3: Rank and evaluate hypotheses
        ranked = self.ranker.evaluate_hypotheses(
            self.generated_hypotheses, self.facts, self.kb.domain
        )

        # Record ranking results in chain
        self.chain.add_step(
            ReasoningStepType.HYPOTHESIS_RANKED,
            f"Evaluated {len(ranked.all_hypotheses)} hypotheses",
            output_data={
                h.hypothesis_id: f"{h.posterior_confidence:.0%} ({h.status})"
                for h in ranked.all_hypotheses
            },
        )

        # Step 4: Record root cause
        self.chain.add_step(
            ReasoningStepType.ROOT_CAUSE_SELECTED,
            ranked.diagnosis_summary,
            confidence=ranked.confidence,
            output_data={
                "root_cause": ranked.root_cause_desc or "Not determined",
                "confidence": f"{ranked.confidence:.0%}",
                "conclusive": str(ranked.is_conclusive),
            },
        )

        if not ranked.root_cause_id:
            return None

        # Step 5: Generate recommendations
        fixes = self._generate_fixes(ranked.root_cause_id)

        diagnosis = Diagnosis(
            category=self.kb.domain,
            root_cause=ranked.root_cause_desc or "Unknown",
            confidence=ranked.confidence,
            recommended_fixes=fixes,
            explanation=self.chain.render_text(),
        )

        session.diagnosis = diagnosis
        session.reasoning_chain = self.chain

        return diagnosis

    # ------------------------------------------------------------------
    # SERVICE NAME EXTRACTION
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_service_name(query: str) -> str | None:
        """Attempt to extract a known service name from the user's query."""
        query_lower = query.lower()
        for service in _COMMON_SERVICES:
            if service in query_lower:
                return service
        return None

    # ------------------------------------------------------------------
    # MULTI-HOP FORWARD CHAINING
    # ------------------------------------------------------------------

    def _forward_chain(self, initial_rules: list[KBRule]) -> None:
        """
        Multi-hop forward chaining loop.

        Each iteration:
        1. Find all fireable rules (not yet fired, conditions match)
        2. Fire the highest-priority rule
        3. New facts may match additional rules
        4. Continue until no fireable rules or MAX_ITERATIONS
        """
        # Sort once by priority desc
        rule_queue = sorted(initial_rules, key=lambda r: -r.priority)
        iteration = 0

        while rule_queue and iteration < self.MAX_ITERATIONS:
            iteration += 1
            rule = rule_queue.pop(0)

            if rule.rule_id in self.fired_rules:
                continue

            log.info(f"\n[bold]Iteration {iteration}: Rule[/bold] [{rule.rule_id}] {rule.name}")
            self.chain.add_step(
                ReasoningStepType.RULE_FIRED,
                f"Fired rule [{rule.rule_id}] {rule.name}",
                input_data={"trigger_symptoms": rule.trigger_symptoms},
            )

            self.fired_rules.add(rule.rule_id)

            # Execute the rule: collect evidence
            new_facts = self._execute_rule(rule)

            # If this rule produced new facts, check if more rules can fire
            if new_facts and iteration < self.MAX_ITERATIONS:
                additional_rules = self._find_additional_rules(rule_queue)
                rule_queue.extend(additional_rules)
                rule_queue.sort(key=lambda r: -r.priority)

    def _execute_rule(self, rule: KBRule) -> dict[str, str]:
        """Execute a single rule: collect evidence, produce facts, generate hypotheses."""
        new_facts: dict[str, str] = {}

        for step in rule.evidence_gathering:
            _, extracted = self._gather_evidence(step.command, step.parser_regex)
            self.facts[step.fact_key] = extracted
            new_facts[step.fact_key] = extracted

            self.chain.add_step(
                ReasoningStepType.EVIDENCE_COLLECTED,
                f"Collected evidence: {step.command}",
                input_data={"command": step.command},
                output_data={step.fact_key: extracted},
            )

            log.info(f"    Fact: [magenta]{step.fact_key}[/magenta] = '{extracted}'")

        # Evaluate RCA conditions
        for rca in rule.root_cause_analysis:
            condition_met = self._evaluate_condition(rca.condition, self.facts)

            # Also check after_condition if the RCA entry has one
            after_met = True
            if rca.after_condition is not None:
                after_met = self._evaluate_condition(rca.after_condition, self.facts)

            if condition_met and after_met:
                resolved_cause = self._resolve_template(rca.root_cause, self.facts)
                log.info(f"[bold green]Hypothesis confirmed:[/bold green] {resolved_cause}")
                hyp = {
                    "id": rca.hypothesis_id,
                    "description": resolved_cause,
                    "confidence": 0.95,
                    "is_confirmed": True,
                }
                self.generated_hypotheses.append(hyp)

                self.chain.add_step(
                    ReasoningStepType.HYPOTHESIS_CONFIRMED,
                    f"Confirmed: {resolved_cause}",
                    confidence=0.95,
                    output_data={"hypothesis_id": rca.hypothesis_id},
                )
            else:
                # Generate as active hypothesis for ranking
                for h in rule.hypotheses:
                    if h.id == rca.hypothesis_id:
                        self.generated_hypotheses.append({
                            "id": h.id,
                            "description": h.description,
                            "confidence": h.confidence,
                        })
                        self.chain.add_step(
                            ReasoningStepType.HYPOTHESIS_GENERATED,
                            f"Generated hypothesis: {h.description}",
                            confidence=h.confidence,
                            output_data={"hypothesis_id": h.id},
                        )

        return new_facts

    def _find_additional_rules(self, remaining: list[KBRule]) -> list[KBRule]:
        """Find additional rules that can fire based on new facts."""
        additional = []
        for rule in remaining:
            if rule.rule_id in self.fired_rules:
                continue
            # Check if any trigger symptom is satisfied by current facts
            for step in rule.evidence_gathering:
                if step.fact_key in self.facts:
                    additional.append(rule)
                    break
        return additional

    # ------------------------------------------------------------------
    # EVIDENCE COLLECTION
    # ------------------------------------------------------------------

    def _gather_evidence(self, command: str, parser_regex: str) -> tuple[Evidence, str]:
        """Execute a command and extract value via regex."""
        log.info(f"  [cyan]Running:[/cyan] {command}")
        try:
            evidence = self.executor.execute(command)
        except UnsafeCommandError as e:
            log.error(f"  [red]Blocked unsafe command: {e}[/red]")
            return Evidence(command_run=command, stdout="", stderr=str(e), return_code=1), ""

        extracted_value = ""
        if evidence.stdout:
            match = re.search(parser_regex, evidence.stdout)
            if match:
                groups = match.groupdict()
                if groups:
                    extracted_value = " ".join(v for v in groups.values() if v is not None)
                elif match.lastindex:
                    extracted_value = match.group(1)

        return evidence, extracted_value

    # ------------------------------------------------------------------
    # SYMPTOM MATCHING
    # ------------------------------------------------------------------

    def _match_symptoms(self, user_query: str) -> list[KBRule]:
        """Find all rules whose trigger symptoms match the user query."""
        query_lower = user_query.lower()
        matched = []
        for rule in self.kb.rules:
            matched_symptoms = [s for s in rule.trigger_symptoms if s.lower() in query_lower]
            if matched_symptoms:
                matched.append(rule)
                self.chain.add_step(
                    ReasoningStepType.SYMPTOM_MATCHED,
                    f"Matched [{rule.rule_id}]: {', '.join(matched_symptoms)}",
                    input_data={"query": user_query},
                    output_data={"matched_symptoms": matched_symptoms},
                )
        return matched

    # ------------------------------------------------------------------
    # CONDITION EVALUATION
    # ------------------------------------------------------------------

    def _evaluate_condition(self, condition: RcaCondition, facts: dict[str, str]) -> bool:
        """Evaluate a single condition against fact store."""
        fact_value = facts.get(condition.fact, "")
        op = condition.operator
        ref = condition.value

        match op:
            case "contains":
                return ref.lower() in fact_value.lower()
            case "not_contains":
                return ref.lower() not in fact_value.lower()
            case "equals":
                return fact_value.strip() == ref.strip()
            case "not_equals":
                return fact_value.strip() != ref.strip()
            case "is_empty":
                return not fact_value.strip()
            case "is_not_empty":
                return bool(fact_value.strip())
            case "greater_than":
                try:
                    return float(fact_value) > float(ref)
                except ValueError:
                    return False
            case _:
                log.warning(f"Unknown operator: '{op}'")
                return False

    # ------------------------------------------------------------------
    # FIX GENERATION
    # ------------------------------------------------------------------

    def _generate_fixes(self, root_cause_id: str) -> list[CommandRecommendation]:
        """Generate fix recommendations for identified root cause."""
        fixes = []
        for rule in self.kb.rules:
            for rca in rule.root_cause_analysis:
                if rca.hypothesis_id == root_cause_id:
                    for fix in rca.recommended_fixes:
                        resolved_cmd = self._resolve_template(fix["command"], self.facts)
                        resolved_expl = self._resolve_template(fix["explanation"], self.facts)
                        self.chain.add_step(
                            ReasoningStepType.RECOMMENDATION_GENERATED,
                            f"Fix: {resolved_expl}",
                            output_data={"command": resolved_cmd, "risk": "moderate"},
                        )
                        fixes.append(CommandRecommendation(
                            command=resolved_cmd,
                            explanation=resolved_expl,
                            is_safe_to_auto_run=fix.get("is_safe", False),
                        ))
        return fixes

    def get_reasoning_chain(self) -> ReasoningChain:
        """Return the reasoning chain for explainability."""
        return self.chain
