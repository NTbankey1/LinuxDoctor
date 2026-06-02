"""Knowledge Base loader and parser module."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from linux_doctor.infrastructure.logger import log


class EvidenceStep(BaseModel):
    """Defines a command to run to gather evidence for a hypothesis."""

    hypothesis_id: str
    command: str
    parser_regex: str
    fact_key: str


class RcaCondition(BaseModel):
    """A condition to evaluate against collected facts."""

    fact: str
    operator: str  # "contains", "not_contains", "equals", "not_equals", "is_empty", "is_not_empty", "greater_than"
    value: str


class RcaEntry(BaseModel):
    """Maps a hypothesis to its root cause and recommended fixes."""

    hypothesis_id: str
    condition: RcaCondition
    root_cause: str
    recommended_fixes: list[dict[str, Any]] = Field(default_factory=list)
    after_condition: RcaCondition | None = None


class HypothesisDef(BaseModel):
    """A potential cause defined in the Knowledge Base."""

    id: str
    description: str
    confidence: float


class KBRule(BaseModel):
    """A single diagnostic rule loaded from a YAML Knowledge Base file."""

    rule_id: str
    name: str
    priority: int
    trigger_symptoms: list[str]
    hypotheses: list[HypothesisDef]
    evidence_gathering: list[EvidenceStep]
    root_cause_analysis: list[RcaEntry]


class DomainKnowledgeBase(BaseModel):
    """Represents the entire knowledge base for a specific Linux domain."""

    domain: str
    version: str
    description: str
    rules: list[KBRule]


class KnowledgeBaseLoader:
    """Loads and validates YAML knowledge base files from the kb directory."""

    def __init__(self, kb_path: str = "data/kb") -> None:
        """Initialize the loader with the path to the KB directory."""
        self.kb_path = Path(kb_path)
        self._cache: dict[str, DomainKnowledgeBase] = {}

    def load_domain(self, domain: str) -> DomainKnowledgeBase | None:
        """
        Load and parse the knowledge base for a given domain.

        Args:
            domain: The domain name (e.g., 'docker', 'nginx', 'ssh').

        Returns:
            A validated DomainKnowledgeBase object, or None if not found.
        """
        if domain in self._cache:
            return self._cache[domain]

        kb_file = self.kb_path / f"{domain}.yaml"

        if not kb_file.exists():
            log.warning(f"[yellow]No knowledge base found for domain: '{domain}'[/yellow]")
            return None

        try:
            with open(kb_file) as f:
                raw_data = yaml.safe_load(f)
            kb = DomainKnowledgeBase(**raw_data)
            self._cache[domain] = kb
            log.debug(f"Loaded KB for domain '{domain}': {len(kb.rules)} rules.")
            return kb
        except Exception as e:
            log.error(f"[red]Failed to parse KB file '{kb_file}': {e}[/red]")
            return None

    def list_available_domains(self) -> list[str]:
        """Return a list of all domains with available KB files."""
        return [f.stem for f in self.kb_path.glob("*.yaml")]
