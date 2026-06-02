# Linux Doctor — Hybrid AI Linux Troubleshooting

![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python)
![AI](https://img.shields.io/badge/AI-Classical+LLM%20Hybrid-success)
![ML](https://img.shields.io/badge/ML-From%20Scratch-orange)
![Tests](https://img.shields.io/badge/Tests-143%20Passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)

> **Describe any Linux issue in natural language — Linux Doctor diagnoses root causes, explains reasoning, and suggests safe fixes.**

```bash
linux-doctor "nginx failed to start"
# → Domain: NGINX (82% confidence)
# → Root Cause: Nginx is not installed on this system
# → Fix: sudo apt-get install nginx -y
```

> **One-line install (Linux/macOS):**
> ```bash
> curl -fsSL https://raw.githubusercontent.com/NTbankey1/LinuxDoctor/main/scripts/install.sh | bash
> ```

---

## Quick Start — Choose Your Path

### Easiest — One-liner (no prerequisites needed)

```bash
curl -fsSL https://raw.githubusercontent.com/NTbankey1/LinuxDoctor/main/scripts/install.sh | bash
```

This installs everything: Python dependencies, trained ML models, dataset, and the `linux-doctor` command. Works on any system with `git`, `curl`, and Python 3.10+.

Then use:

```bash
linux-doctor "docker permission denied"
```

### Via uv (if you already have it)

```bash
pip install linux-doctor  # not yet on PyPI — use the one-liner above or clone directly
```

### Manual (clone + setup)

```bash
git clone https://github.com/NTbankey1/LinuxDoctor.git
cd linux-doctor
make setup
linux-doctor "disk is full on /var"
```

> **Note:** Pre-trained ML models are shipped with the repository. No training required unless you want to retrain. To retrain: `make train-dataset`.

---

## Key Capabilities

| Capability | How |
|---|---|
| **Understand natural language** | English + Vietnamese, technical + casual |
| **Detect the domain** | ML classifier (3 algorithms from scratch, 12 domains) |
| **Diagnose root cause** | Forward-chaining rule engine with YAML knowledge base |
| **Collect evidence** | Safe shell execution with regex parsing |
| **Rank hypotheses** | Bayesian confidence scoring |
| **Explain reasoning** | Full audit trail of every diagnostic step |
| **Interactive REPL** | Rich terminal UI with command history |

All ML models are implemented **from scratch** (NumPy only) — no sklearn, no PyTorch, no LLM required for core diagnosis.

---

## Examples

```bash
# One-shot diagnosis
linux-doctor "nginx failed to start"
linux-doctor "disk is full on /var"
linux-doctor "ssh connection refused port 22"
linux-doctor "docker container keeps restarting"
linux-doctor "cannot install package nginx"

# Interactive REPL
linux-doctor
# → Type your issue naturally
# → Type /help for commands
```

### REPL Commands

| Command | What it does |
|---|---|
| `/explain` | Show full reasoning chain |
| `/history` | Show past diagnoses |
| `/fix` | List available fix commands |
| `/fix [n]` | Execute fix step n |
| `/safe` | Toggle safe mode |
| `/help` | Show all commands |
| `/exit` | Quit |

---

## Architecture

```
User Input
  │
  ▼ ML Classifier (TF-IDF + Linear SVM / NB / LR)
Domain detected
  │
  ▼ Forward-Chaining Rule Engine
Evidence gathered via safe shell commands
  │
  ▼ Hypothesis Ranker (Bayesian)
Root cause identified
  │
  ▼ Remediation Pipeline
Fix suggestions + safe execution
  │
  ▼ Verification
Fix verified or rolled back
```

```
src/linux_doctor/
├── cli/              # CLI entry point + REPL
├── domain/           # Data models (Session, Hypothesis, Evidence…)
├── engines/          # Rule engine + hypothesis ranker + reasoning chain
├── evidence/         # Evidence collector (execution + parsing)
├── graph/            # Cross-domain knowledge graph
├── incident/         # Incident lifecycle management
├── infrastructure/   # Shell execution, KB loading, database, logging
├── ml/               # From-scratch ML (Naive Bayes, LR, SVM, TF-IDF)
├── preprocessing/    # Text preprocessing pipeline
├── remediation/      # Safe fix execution + rollback
└── verification/     # Fix verification engine
```

---

## ML Model Performance

**Dataset**: 100,000+ synthetically generated Linux issue samples (balanced across 12 domains)

| Domain | Samples |
|---|---|
| docker | ~8,500 |
| nginx | ~8,500 |
| ssh | ~8,500 |
| disk | ~8,500 |
| memory | ~8,500 |
| cpu | ~8,500 |
| network | ~8,500 |
| dns | ~8,500 |
| git | ~8,500 |
| package | ~8,500 |
| systemd | ~8,500 |
| permission | ~8,500 |

**Note**: The 96%+ F1 scores on synthetic data are a starting point. Real-world accuracy is our current focus — see [Roadmap](docs/roadmap-2026.md).

---

## Roadmap

| Phase | Target | Description |
|---|---|---|
| **Level 1** | Now | Diagnostic tool (classifier + rule engine + evidence) |
| **Level 2** | 2026 | Terminal copilot (remediation + verification + incident management) |
| **Level 3** | 2027 | Terminal agent (memory + planning + local LLM) |
| **Level 4** | 2028 | Autonomous Linux engineer (anomaly detection + auto-remediation) |
| **Level 5** | 2029-30 | Fleet operations platform (multi-host + correlation) |
| **Level 6** | 2030+ | Fleet intelligence (prediction + autonomous optimization) |

Full details: [docs/roadmap-2026.md](docs/roadmap-2026.md)

---

## Documentation

| Document | What it covers |
|---|---|
| [Roadmap 2026-2031](docs/roadmap-2026.md) | Full 5-year product & architecture plan |
| [Architecture Design](docs/architecture_design.md) | System design & data flow |
| [ML Design (Academic)](docs/ml_from_scratch_design.md) | Math formulas & algorithm derivations |
| [Domain Analysis](docs/domain-analysis.md) | Linux troubleshooting domain model |

---

## Contributing

This project is in active development. Contributions welcome:

- **Knowledge Base**: Add YAML rules for new Linux issue patterns
- **ML**: Improve classifier accuracy, add domains
- **Safety**: Strengthen command allowlist and danger detection
- **Tests**: Add test cases for edge cases

See [docs/roadmap-2026.md](docs/roadmap-2026.md) for current priorities.

---

## License

MIT — free for any use, commercial or personal.

---

*Built for Linux Sysadmins, SREs, DevOps Engineers, and AI enthusiasts.*
