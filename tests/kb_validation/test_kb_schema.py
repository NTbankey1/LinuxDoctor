"""Knowledge Base integrity validation — every KB file is checked."""

from __future__ import annotations

import pytest
import yaml

from linux_doctor.infrastructure.kb_loader import KnowledgeBaseLoader


class TestKBSchemaCompliance:
    """Structural validation of all YAML KB files."""

    KB_DIR = "data/kb"
    REQUIRED_TOP = {"domain", "version", "description", "rules"}

    @pytest.fixture(scope="class")
    def loader(self):
        return KnowledgeBaseLoader(self.KB_DIR)

    @pytest.fixture(params=[
        "cpu", "disk", "dns", "docker", "git", "memory",
        "network", "nginx", "package", "permissions", "ssh", "systemd",
    ])
    def kb_file(self, request, loader):
        return loader.load_domain(request.param)

    @pytest.fixture(scope="class")
    def raw_kb_files(self):
        """Load raw YAML for structural checks."""
        from pathlib import Path
        files = {}
        for f in Path(self.KB_DIR).glob("*.yaml"):
            with open(f) as fh:
                files[f.stem] = yaml.safe_load(fh)
        return files

    def test_all_domains_load(self, loader):
        domains = loader.list_available_domains()
        assert len(domains) == 12, f"Expected 12 KB files, found {len(domains)}"

    def test_required_top_level_fields(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            missing = self.REQUIRED_TOP - set(kb.keys())
            assert not missing, f"{domain}.yaml: missing {missing}"

    def test_no_duplicate_rule_ids(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            ids = [r["rule_id"] for r in kb.get("rules", [])]
            dups = [rid for rid in ids if ids.count(rid) > 1]
            assert not dups, f"{domain}.yaml duplicate rule_ids: {set(dups)}"

    def test_every_rule_has_hypotheses(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                assert len(rule.get("hypotheses", [])) > 0, (
                    f"{domain}.yaml: {rule['rule_id']} has no hypotheses"
                )

    def test_every_hypothesis_has_evidence(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                assert len(rule.get("evidence_gathering", [])) > 0, (
                    f"{domain}.yaml: {rule['rule_id']} has no evidence_gathering"
                )

    def test_every_rule_has_rca(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                assert len(rule.get("root_cause_analysis", [])) > 0, (
                    f"{domain}.yaml: {rule['rule_id']} has no root_cause_analysis"
                )

    def test_every_rca_has_fixes(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                for rca in rule.get("root_cause_analysis", []):
                    assert len(rca.get("recommended_fixes", [])) > 0, (
                        f"{domain}.yaml: {rca.get('hypothesis_id')} has no fixes"
                    )

    def test_priorities_in_range(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                pri = rule.get("priority", 0)
                assert 1 <= pri <= 10, f"{domain}.yaml: {rule['rule_id']} priority {pri}"

    def test_no_destructive_commands_in_evidence(self, raw_kb_files):
        import re
        # These patterns must NOT appear as standalone commands in evidence
        destructive = [r'\brm\s', r'\bmkfs\.', r'\bdd\s', r'\|\s*bash\b', r'\|\s*sh\b']
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                for step in rule.get("evidence_gathering", []):
                    cmd = step.get("command", "")
                    for pattern in destructive:
                        if re.search(pattern, cmd):
                            raise AssertionError(
                                f"{domain}.yaml: Evidence matches destructive pattern '{pattern}': {cmd[:80]}"
                            )

    def test_hypothesis_confidence_in_range(self, raw_kb_files):
        for domain, kb in raw_kb_files.items():
            for rule in kb.get("rules", []):
                for hyp in rule.get("hypotheses", []):
                    conf = hyp.get("confidence", 0)
                    assert 0.0 <= conf <= 1.0, (
                        f"{domain}.yaml: {hyp['id']} confidence {conf}"
                    )
