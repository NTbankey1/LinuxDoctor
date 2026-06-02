"""Tests for the Knowledge Base loader."""

from __future__ import annotations

import pytest

from linux_doctor.infrastructure.kb_loader import KnowledgeBaseLoader


class TestKnowledgeBaseLoader:
    @pytest.fixture
    def loader(self):
        return KnowledgeBaseLoader("data/kb")

    def test_list_domains(self, loader):
        domains = loader.list_available_domains()
        assert len(domains) >= 3, f"Expected >=3 domains, got {len(domains)}"
        for required in ("docker", "nginx", "ssh"):
            assert required in domains, f"Missing {required}"

    def test_load_docker(self, loader):
        kb = loader.load_domain("docker")
        assert kb is not None
        assert kb.domain == "docker"
        assert len(kb.rules) > 0

    def test_load_nginx(self, loader):
        kb = loader.load_domain("nginx")
        assert kb is not None
        assert kb.domain == "nginx"

    def test_load_ssh(self, loader):
        kb = loader.load_domain("ssh")
        assert kb is not None
        assert kb.domain == "ssh"

    def test_load_nonexistent(self, loader):
        kb = loader.load_domain("nonexistent_domain")
        assert kb is None

    def test_cache_works(self, loader):
        kb1 = loader.load_domain("docker")
        kb2 = loader.load_domain("docker")
        assert kb1 is kb2  # Same object from cache

    def test_each_domain_has_rules(self, loader):
        for domain in loader.list_available_domains():
            kb = loader.load_domain(domain)
            assert len(kb.rules) > 0, f"{domain} has no rules"

    def test_each_rule_has_trigger_symptoms(self, loader):
        for domain in loader.list_available_domains():
            kb = loader.load_domain(domain)
            for rule in kb.rules:
                assert len(rule.trigger_symptoms) > 0, f"{domain}: {rule.rule_id} no symptoms"

    def test_each_rule_has_evidence(self, loader):
        for domain in loader.list_available_domains():
            kb = loader.load_domain(domain)
            for rule in kb.rules:
                assert len(rule.evidence_gathering) > 0, f"{domain}: {rule.rule_id} no evidence"

    def test_each_rule_has_rca(self, loader):
        for domain in loader.list_available_domains():
            kb = loader.load_domain(domain)
            for rule in kb.rules:
                assert len(rule.root_cause_analysis) > 0, f"{domain}: {rule.rule_id} no RCA"

    def test_each_rca_has_fixes(self, loader):
        for domain in loader.list_available_domains():
            kb = loader.load_domain(domain)
            for rule in kb.rules:
                for rca in rule.root_cause_analysis:
                    assert len(rca.recommended_fixes) > 0, f"{domain}: {rca.hypothesis_id} no fixes"
