# Linux Doctor — Pre-Release System Report

**Version:** 0.1.0
**Date:** 2026-06-01
**Status:** ✅ READY FOR PUBLICATION

---

## 1. System Overview

```
Linux Doctor — Classical AI Linux Troubleshooting Expert System

Architecture:
  Natural Language → ML Domain Classifier → Expert System → Evidence Collection → RCA → Diagnosis → Fix

Key Features:
  ✓ 100% local, zero external API dependencies
  ✓ All ML algorithms implemented from scratch (NumPy only)
  ✓ Expert System with multi-hop forward chaining
  ✓ Bayesian Root Cause Analysis with hypothesis ranking
  ✓ Allowlist-based safety system for command execution
  ✓ Full audit trail (Reasoning Chain)
  ✓ SQLite persistence with incident cache
  ✓ CI/CD pipeline (GitHub Actions)
```

---

## 2. ML Pipeline (From Scratch)

| Component | Implementation | Lines |
|-----------|---------------|-------|
| Text Preprocessing | Tokenizer + stopword filter + domain-preserve terms | 168 |
| TF-IDF Vectorizer | Smooth IDF, L2 normalization, max_features=3000 | 180 |
| Naive Bayes | Laplace smoothing, log-space probabilities | 139 |
| Logistic Regression | Softmax + mini-batch GD + L2 regularization | 204 |
| Linear SVM | Hinge loss + One-vs-Rest + Subgradient SGD | 213 |
| BM25 Retrieval | Okapi BM25 from scratch, zero dependencies | 168 |
| Training Pipeline | Automated training + evaluation + model serialization | 152 |
| Evaluation | Accuracy, precision, recall, F1, confusion matrix | 148 |

**Best Model:** Linear SVM (Weighted F1: 99.27%)

---

## 3. Expert System

| Component | Lines | Description |
|-----------|-------|-------------|
| Rule Engine | 370 | Multi-hop forward chaining, max 50 iterations |
| Hypothesis Ranker | 390 | Bayesian belief update, evidence-specific weighting, margin threshold |
| Reasoning Chain | 170 | Full audit trail (symptom → rule → evidence → hypothesis → fix) |
| KB Loader | 108 | YAML parsing with Pydantic validation, in-memory caching |

---

## 4. Knowledge Base Coverage

| Domain | Rules | Hypotheses | Evidence Steps | Fixes |
|--------|-------|-----------|----------------|-------|
| systemd | 6 | 7 | 17 | 18 |
| docker | 6 | 10 | 16 | 19 |
| permissions | 5 | 7 | 13 | 15 |
| nginx | 5 | 9 | 13 | 22 |
| package | 4 | 7 | 13 | 13 |
| git | 4 | 6 | 12 | 14 |
| disk | 4 | 7 | 13 | 18 |
| network | 3 | 7 | 11 | 16 |
| cpu | 3 | 4 | 10 | 10 |
| memory | 3 | 7 | 10 | 13 |
| ssh | 3 | 6 | 9 | 17 |
| dns | 2 | 4 | 8 | 8 |
| **Total** | **48** | **81** | **145** | **183** |

---

## 5. Security Architecture

**3-Layer Safety System:**

| Layer | Check | Example Blocked |
|-------|-------|-----------------|
| 1. Allowlist | Only approved commands | `python3`, `ruby`, `perl` |
| 2. Dangerous Patterns | 8 regex patterns | `rm -rf /`, `dd if=/dev/zero` |
| 3. Shell Metacharacters | `` ` ``, `$()` | `` echo `whoami` `` |

**Shell Execution:**
- `preexec_fn=os.setpgrp` — no zombie processes
- Timeout with SIGKILL fallback
- Output size limit (1MB)
- Separated exception handlers (not bare `except`)

---

## 6. Database Schema

8 tables, SQLite with WAL mode:

| Table | Rows | Purpose |
|-------|------|---------|
| sessions | Per diagnosis | User query, domain, status, duration |
| symptoms | Per symptom | Detected symptom IDs and scores |
| evidence | Per command | Command, exit code, stdout, stderr |
| hypotheses | Per hypothesis | Bayesian scores, status, elimination |
| diagnoses | Per session | Root cause, confidence, margin |
| recommendations | Per fix | Fix commands, risk level, applied status |
| rule_firings | Per rule fire | Rule ID, iteration, conditions |
| incident_cache | Per unique issue | Query hash, frequency, last seen |

---

## 7. Test Results

```
81 tests passed, 0 failed, 0 lint errors

Coverage by module:
  Rule Engine:         53 tests (comprehensive: matching, conditions, chaining)
  Shell Runner:        11 tests (allowlist, dangerous patterns, safety)
  BM25:                10 tests (indexing, search, ranking, empty edge cases)
  Database:             7 tests (CRUD, incident cache, empty state)
  KB Validation:       All 12 domains validated on load
```

---

## 8. Project Metrics

| Metric | Value |
|--------|-------|
| Source files | 30 Python files |
| Source LOC | ~3,500 |
| Test files | 5 files |
| Test LOC | ~900 |
| KB YAML files | 12 domains |
| KB YAML size | 148 KB |
| Dataset samples | 6,200 labeled |
| Training samples used | 12,427 (unique dedup) |
| ML classes | 12 Linux domains |
| Best model accuracy | 99.27% (Linear SVM) |
| GitHub Actions | CI configured (lint + test + KB validate) |

---

## 9. Quick Start

```bash
# Install
git clone https://github.com/<user>/linux-doctor
cd linux-doctor
uv sync

# Train ML model (optional — pre-trained models included)
uv run python -m linux_doctor.ml.trainer

# Diagnose an issue
uv run python -m linux_doctor.cli.app "nginx failed to start"

# Run tests
uv run pytest

# Lint check
uv run ruff check src/ tests/
```

---

## 10. Known Limitations

| Issue | Impact | Planned Fix |
|-------|--------|-------------|
| ML confidence low for short queries (<5 tokens) | Domain correct but confidence < 50% | Keyword override already implemented |
| No backward chaining (interactive questions) | Some inconclusive diagnoses | Requires new module |
| OS commands assume Ubuntu/Debian | Fedora/Arch may have different paths | OSProfile abstraction needed |
| No JSON output mode | Cannot integrate with other tools | Output formatter needed |
| No remote diagnosis (SSH target) | Local machine only | Future feature |
| Dataset is synthetic | Real-world edge cases may be missed | Community contributions |
