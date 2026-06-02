# 🐧 Linux Doctor - Hybrid AI Troubleshooting Assistant

![Python](https://img.shields.io/badge/Python-3.13+-3776AB.svg?logo=python)
![AI](https://img.shields.io/badge/AI-Classical%20Only-success)
![ML](https://img.shields.io/badge/ML-From%20Scratch-orange)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)

> **A Linux troubleshooting expert system built on Classical AI — no LLMs, no GPUs, no black boxes.**

---

## 🧠 What Makes This Different?

While everyone is wrapping GPT/Claude in a chatbot, **Linux Doctor** implements the entire AI pipeline from mathematical first principles:

| Component | Technology | Implementation |
|---|---|---|
| **Text Processing** | Tokenizer + Porter-lite Stemmer | From scratch (zero NLP libs) |
| **Feature Extraction** | TF-IDF with smooth IDF | From scratch (NumPy only) |
| **Classifier 1** | Multinomial Naive Bayes | From scratch (Laplace smoothing) |
| **Classifier 2** | Logistic Regression | From scratch (Softmax + mini-batch GD) |
| **Classifier 3** | Linear SVM | From scratch (Hinge loss + Subgradient SGD) |
| **Expert System** | Forward Chaining Rule Engine | From scratch (YAML Knowledge Base) |
| **Evidence Engine** | Safe Shell Execution + Regex parsing | Sandboxed subprocess |

---

## ✨ How It Works

```
Input: "docker permission denied"
  │
  ▼  TF-IDF + Linear SVM (from scratch)
Domain: DOCKER  (Confidence: 82%)
  │
  ▼  Forward Chaining Rule Engine
Hypothesis: user_not_in_docker_group
  │
  ▼  Evidence Engine: runs `groups` safely
Fact: user_groups = "sudo ntbankey"  ← 'docker' missing
  │
  ▼  Root Cause Analysis
Root Cause: User is not in the 'docker' group.
  │
  ▼  CLI Output
Fix: sudo usermod -aG docker $USER
```

---

## 🚀 Quick Start

```bash
# Install (requires Python 3.13+ and uv)
git clone https://github.com/your/linux-doctor && cd linux-doctor
make setup

# Train all ML models (Naive Bayes, Logistic Regression, Linear SVM)
uv run python -m linux_doctor.ml.trainer

# Run Linux Doctor
uv run python -m linux_doctor.cli.app "nginx failed to start"

# Run tests
make test
```

---

## 📊 ML Model Results (6000-sample dataset)

| Algorithm | Weighted F1 | Accuracy |
|---|---|---|
| **Naive Bayes** 🏆 | **0.997** | **99.7%** |
| **Linear SVM** | **0.997** | **99.7%** |
| Logistic Regression | 0.996 | 99.6% |

---

## 📚 Documentation

| Document | Description |
|---|---|
| [Architecture Design](docs/architecture_design.md) | System design & data flow |
| [ML Design (Academic)](docs/ml_from_scratch_design.md) | Math formulas & algorithm derivations |
| [Implementation Plan](docs/unified_implementation_plan.md) | Phase status & project structure |
| [Skill Matrix](docs/skills.md) | Skills required to build this project |

---

## 🏗️ Project Structure

```
linux-doctor/
├── src/linux_doctor/
│   ├── domain/          # Pure data models (Fact, Rule, Hypothesis)
│   ├── infrastructure/  # Shell executor, KB loader, Logger
│   ├── ml/              # All ML algorithms (from scratch)
│   ├── engines/         # Forward Chaining Rule Engine
│   └── cli/             # Rich TUI interface
├── data/
│   ├── raw/             # Training dataset (JSONL)
│   └── kb/              # Expert knowledge base (YAML)
└── models/              # Trained model artifacts (pickle)
```

---

## 🎓 Academic Value

This project demonstrates deep understanding of:
- **Information Retrieval:** TF-IDF derivation and implementation
- **Probabilistic ML:** Bayesian inference, Laplace smoothing
- **Optimization:** Gradient descent, subgradient methods, learning rate scheduling
- **Knowledge Engineering:** Ontology design, rule-based reasoning
- **Systems Programming:** Safe subprocess execution, parsing, regex

---

*Built with ❤️ for Linux Sysadmins, DevOps Engineers, and AI enthusiasts.*
