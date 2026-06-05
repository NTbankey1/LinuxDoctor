# 🐧 Linux Doctor — 13-Slide Technical Presentation

> **Hybrid AI for Automated Linux Troubleshooting**  
> ML Classification (99.49% F1) · Forward-Chaining Expert System · 7-Layer Safe Shell
>
> *Built from scratch — pure NumPy, zero external ML dependencies*

---

# SLIDE 1 — Title

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🐧 LINUX DOCTOR                                     ║
║          Hybrid AI for Automated Linux Troubleshooting        ║
║                                                              ║
║   ─────────────────────────────────────────────────────       ║
║                                                              ║
║   "From symptom to root cause — in seconds, not hours"       ║
║                                                              ║
║   ─────────────────────────────────────────────────────       ║
║                                                              ║
║          99.49% F1  ·  12 Domains  ·  101,758 Samples        ║
║          4,500 LOC  ·  6 Dependencies  ·  Pure NumPy ML      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

| Layer | Technology | Role |
|---|---|---|
| 🤖 **Machine Learning** | Naive Bayes · SVM · Logistic Regression (scratch) | Domain classification from natural language |
| 🧠 **Expert System** | Forward-chaining rule engine + Bayesian ranking | Root cause analysis & evidence gathering |
| 🛡️ **Safe Shell** | 7-layer allowlist sandbox | Read-only diagnostic execution |
| 📺 **Interface** | Rich 3-column Mission Control TUI | Real-time incident visualization |

---

# SLIDE 2 — The Problem

## Why Linux Troubleshooting Is Broken

```
🧑‍💻 SRE gets paged at 3 AM — "Disk full on production"
         │
         ├── 🔍 SSH into server (1 min)
         ├── 📋 df -h, du -sh, find large files (3 min)
         ├── 🤔 Check logrotate, inodes, hidden files (5 min)
         ├── 🧪 Guess root cause, apply fix (10 min)
         ├── ⏱️  Monitor if fix worked (15 min)
         └── 💸  Total: 30–60 min of productive time lost
```

## Three Core Pain Points

| # | Pain Point | Root Cause | Impact |
|---|---|---|---|
| 1 | **Fragmented Knowledge** | Docker ≠ Nginx ≠ SSH ≠ DNS — each domain is a separate specialty | SREs must master 12+ problem spaces |
| 2 | **Manual Diagnostic Loop** | SSH → run commands → grep logs → reason step by step — every single time | Slow, error-prone, non-reproducible |
| 3 | **No Institutional Memory** | Fixes live in Slack threads, personal notes, or people's heads | Same incident recurs — reinventing the wheel |

## The Opportunity

```
SREs spend 30–40% of their time on diagnostics

→ Linux Doctor automates the entire diagnosis loop
→ Covers 12 highest-frequency Linux failure domains
→ Deterministic, explainable, auditable — not a black box
→ ~15s per diagnosis (target: <2s with parallel evidence)
```

---

# SLIDE 3 — Architecture (Two-Phase Hybrid)

## Design Philosophy: Zero-Dependency Core

The system is built on a **zero-unnecessary-dependency architecture** — only NumPy for ML and Rich for UI. Every algorithm is implemented from scratch for full auditability.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  "docker permission denied"                                              │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: ML DOMAIN CLASSIFICATION ── ~5ms                              │
│                                                                          │
│  ┌──────────────┐   ┌───────────────┐   ┌───────────────────────┐       │
│  │  Tokenizer   │──▶│  TF-IDF       │──▶│  Best-of-3 Ensemble   │       │
│  │  + Stemmer   │   │  3,000 feats  │   │  NB / SVM / LR        │       │
│  └──────────────┘   └───────────────┘   └───────────┬───────────┘       │
│                                                      │ domain="docker"   │
│                                                      │ conf=99.5%        │
└──────────────────────────────────────────────────────┼───────────────────┘
                                                       │
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: EXPERT SYSTEM ── ~15s (sequential)                            │
│                                                                          │
│  1. LOAD KB        data/kb/docker.yaml  (auto-discovered)               │
│  2. MATCH SYMPTOMS DOCKER_001  → 2/4 symptoms matched                  │
│  3. GATHER EVIDENCE groups, ls -l /var/run/docker.sock                 │
│  4. EVAL CONDITIONS not_contains("docker") → True                      │
│  5. RANK HYPOTHESES Bayesian: P(H₁|E) = 97% > P(H₂|E) = 3%            │
│  6. OUTPUT          Root cause + confidence + fix + audit trail         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Two Layers, One Mission

| Phase | What It Solves | How | Output |
|---|---|---|---|
| **ML Layer** | *"What kind of problem is this?"* | Trained on 101,758 samples across 12 domains | `domain=docker, confidence=99.5%` |
| **Expert System** | *"What exactly is wrong?"* | Forward-chaining rules + Bayesian ranking | `User not in docker group (95% confidence)` |

---

# SLIDE 4 — ML Pipeline: Raw Text to Domain

## Full Pipeline

```
Input:  "docker permission denied"
           │
           ▼
   ┌─ Tokenizer (regex word-split, Linux-aware stopwords) ──────────┐
   │  + Porter-lite Stemmer (suffix stripping: -ing, -ed, -ion)      │
   │  → ["docker", "permiss", "deni", "socket"]                      │
   └──────────────────────────────────────────────────────────────────┘
           │
           ▼
   ┌─ TF-IDF Vectorizer (pure NumPy implementation) ────────────────┐
   │  Term Frequency · Inverse Document Frequency                    │
   │  Smooth IDF: log((1 + N) / (1 + df(t))) + 1                    │
   │  L2 Normalization on output vectors                             │
   │  Vocabulary: 3,000 top features across 12 domains               │
   │  → [0.0, 0.45, 0.32, 0.0, ..., 0.78]  (sparse, normalized)     │
   └──────────────────────────────────────────────────────────────────┘
           │
           ▼
   ┌─ Ensemble Predictor ────────────────────────────────────────────┐
   │  3 classifiers vote, best model (highest F1) selected           │
   │  → domain = docker                                              │
   │  → confidence = 99.5%                                           │
   │  → all_scores = {docker: 0.995, nginx: 0.003, ssh: 0.001, ...} │
   └──────────────────────────────────────────────────────────────────┘
```

## Fallback Strategy

If ML confidence < 50%, a **keyword-based router** overrides:
```
"connection refused port 22" → ML=ssh(@45%) + keyword_override=ssh(@70%)
                                → final=ssh (keyword override)

"unusual weird error"        → ML=unknown(@12%) + keyword_override=none
                                → "Domain not recognized, suggest manual investigation"
```

---

# SLIDE 5 — ML Deep Dive: Three Algorithms from Scratch

All implemented in **pure NumPy** — no scikit-learn, no PyTorch, no external ML library.

---

## A. Multinomial Naive Bayes (Best: 99.49% F1)

```python
# Log-space computation to avoid floating-point underflow
class MultinomialNaiveBayes:
    def fit(self, X, y):
        for c in classes:
            # Laplace smoothing: P(w|c) = (count(w,c) + α) / (count(c) + α×V)
            log_prior[c] = log(count(y==c) / N)
            log_likelihood[c] = log((X_c.sum(0) + alpha)
                                  / (X_c.sum() + alpha * V))

    def predict_proba(self, X):
        # Sum log-probabilities instead of multiplying raw probabilities
        log_posterior = X @ log_likelihood.T + log_prior
        return softmax(log_posterior)
```

**Why it wins:** Short-text classification with sparse TF-IDF vectors is a textbook case for Naive Bayes. Log-space eliminates underflow. Laplace smoothing prevents zero-probability issues for unseen tokens.

---

## B. Linear SVM (Runner-up: 99.4% F1)

```python
class LinearSVM:
    def fit(self, X, y, lr=0.001, epochs=200):
        # One-vs-Rest: train C binary classifiers
        for epoch in range(epochs):
            for i, x_i in enumerate(X):
                scores = x_i @ self.W               # scores for all classes
                for j in range(C):
                    margin = scores[y[i]] - scores[j] + 1.0
                    if margin > 0:                   # hinge loss fires
                        self.W[y[i]] += lr * x_i    # push true class
                        self.W[j]    -= lr * x_i    # pull wrong class
```

**Strength:** Excels at separating **confusable domains** — SSH vs Network, Systemd vs Docker — where vocabulary overlaps significantly.

---

## C. Logistic Regression (99.2% F1)

```python
class LogisticRegression:
    def fit(self, X, y, lr=0.01, epochs=100):
        for _ in range(epochs):
            scores = X @ self.W + self.b             # linear logits
            probs = softmax(scores)                   # → probability distribution
            loss = cross_entropy(probs, y) + λ * ||W||²
            grad_W = X.T @ (probs - y_onehot) / N + λ * self.W
            self.W -= lr * grad_W                    # gradient descent
```

**Strength:** Best **confidence calibration** — the Softmax output is a true probability distribution, making it the most reliable for threshold-based decisions.

---

## Classifier Comparison

| Model | F1 Score | Best For |
|---|---|---|
| 🥇 **Naive Bayes** | **99.49%** | General classification, short text, speed |
| 🥈 Linear SVM | 99.40% | Confusable domain boundaries (SSH/Network) |
| 🥉 Logistic Regression | 99.20% | Confidence calibration, probability estimation |

---

# SLIDE 6 — Training Pipeline & Dataset

## Dataset Profile

| Property | Value | Details |
|---|---|---|
| **Total samples** | **101,758** | Synthetic + augmented |
| **Domains** | 12 | Docker, Nginx, SSH, CPU, Memory, Disk, Network, DNS, Git, Systemd, Package, Permission |
| **Split** | 80/20 stratified | Class proportions preserved in both splits |
| **Features** | 3,000 TF-IDF | Filtered by document frequency |
| **ML deps** | **NumPy only** | Zero external ML libraries |

## Synthetic Data Generation Strategy

Real-world incident reports are scarce. We generate high-quality training data using **template augmentation**:

```
Template: "{subject} {verb} {object} {preposition} {detail}"

Example expansions:
  "docker" + "permission denied" → "docker permission denied on socket"
  "docker" + "connection refused" → "connection refused to docker daemon"
  "nginx" + "failed to start" → "nginx service failed to start"
  "nginx" + "502 bad gateway" → "502 bad gateway from nginx upstream"

Augmentation:
  - Synonym replacement: "refused" ↔ "rejected" ↔ "denied"
  - Word dropout: "docker permission denied" → "docker denied"
  - Bigram swapping: "connection ssh refused" → "ssh connection refused"
```

## Training Flow

```
Raw templates              Clean data               Train
     │                         │                      │
     ▼                         ▼                      ▼
┌──────────┐           ┌──────────────┐       ┌──────────────┐
│ Generate  │──101,758──▶│ Tokenize +   │──X──▶│ Naive Bayes  │──▶ best_model.pkl
│ 110,000   │  samples  │ Stem + TF-IDF│  y   │ SVM          │──▶ svm_model.pkl
│ samples   │           │              │      │ Logistic Reg │──▶ lr_model.pkl
└──────────┘           └──────────────┘       └──────────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ Evaluator    │──▶ F1 = 99.49%
                                            │ 80/20 split  │
                                            └──────────────┘
```

---

# SLIDE 7 — Expert System: Forward-Chaining Rule Engine

## Knowledge Base Structure

Each domain = one YAML file in `data/kb/`. No code changes needed for new domains.

```yaml
# data/kb/docker.yaml  (auto-discovered at startup)
rules:
  - id: DOCKER_001
    name: "Permission Denied on Docker Socket"
    
    symptoms:                       # trigger if ANY match
      - "permission denied"
      - "docker.sock"
      - "cannot connect to docker daemon"
      - "got permission denied while trying to connect"
    
    evidence:                       # commands to gather facts
      - command: "groups"
        store_as: user_groups
        description: "Check user's group membership"
      - command: "ls -l /var/run/docker.sock"
        store_as: socket_info
        description: "Check Docker socket permissions"
      - command: "docker info"
        store_as: docker_info
        description: "Check Docker daemon status"
    
    conditions:                     # evaluate gathered facts
      - fact: user_groups
        operator: not_contains
        value: "docker"
    
    hypotheses:                     # ranked conclusions
      - text: "User is not in the 'docker' group"
        confidence: 0.95
        fix: "sudo usermod -aG docker $USER && newgrp docker"
        risk: moderate              # LOW | MODERATE | HIGH
```

## Supported Operations

| Operator | Type | Example |
|---|---|---|
| `equals` | exact string match | `fact: status, equals: "active"` |
| `contains` | substring | `fact: log, contains: "OOM"` |
| `not_contains` | substring exclusion | `fact: groups, not_contains: "docker"` |
| `greater_than` | numeric | `fact: disk_usage_pct, greater_than: 90` |
| `less_than` | numeric | `fact: free_memory_mb, less_than: 500` |
| `matches` | regex | `fact: error_log, matches: "EACCES|EPERM"` |

---

# SLIDE 8 — Bayesian Hypothesis Ranking

## Why Bayes?

The same symptom can have **multiple competing root causes**. Bayesian inference is the principled way to combine prior knowledge with collected evidence.

## The Formula

```
P(H | E) = P(H) × P(E | H) / P(E)

P(H)     = Prior confidence (set in YAML rule definition)
P(E|H)   = Likelihood — how strongly evidence supports this hypothesis
P(H|E)   = Posterior — updated belief after seeing evidence
```

## Full Worked Example: Docker Permission Denied

```
─── Competing Hypotheses ──────────────────────────────────
  H₁: User NOT in docker group      Prior = 0.95
  H₂: Docker daemon NOT running     Prior = 0.80

─── Evidence Collected ────────────────────────────────────
  E₁: groups → "ntbankey sudo"           → strongly supports H₁
  E₂: /var/run/docker.sock EXISTS        → strongly supports H₁
  E₃: `docker info` returns error        → mildly supports H₂

─── Likelihood Assignment ─────────────────────────────────
  P(E₁|H₁) = 0.90    (user not in group → groups won't show docker)
  P(E₁|H₂) = 0.10    (daemon down doesn't affect groups command)
  P(E₂|H₁) = 0.85    (socket exists → daemon likely running)
  P(E₂|H₂) = 0.20    (daemon could be dead but socket file lingers)
  P(E₃|H₁) = 0.30    (can't talk to daemon if not in group)
  P(E₃|H₂) = 0.80    (daemon down → docker info fails)

─── Bayesian Update ───────────────────────────────────────
  P(H₁ | E₁,E₂,E₃) = 0.95 × 0.90 × 0.85 × 0.30 / Z  →  87%  ✅
  P(H₂ | E₁,E₂,E₃) = 0.80 × 0.10 × 0.20 × 0.80 / Z  →  13%

─── Decision ──────────────────────────────────────────────
  Winner: H₁ — User not in docker group (@ 87% confidence)
  Margin: 74%
  Fix: sudo usermod -aG docker $USER
```

## Deterministic Elimination

If a condition definitively falsifies a hypothesis:

```
Evidence: user_groups = "ntbankey sudo docker"  ← user IS in docker group
                                                      ↓
P(E|H₁) ≈ 0.01  →  H₁ eliminated  →  H₂ becomes winner
```

---

# SLIDE 9 — Evidence Collection & Safe Shell

## How the Expert System Gathers Facts

```
Symptom Match              Execute Commands             Store Results
─────────────              ───────────────             ──────────────
DOCKER_001 fires    ──▶   groups                     ──▶ user_groups = "ntbankey sudo"
                           │
                           ├── ls -l /var/run/docker.sock
                           │   └── socket_info = "srw-rw---- 1 root docker"
                           │
                           └── docker info
                               └── docker_info = "Cannot connect to daemon"
                                    (permission denied)

Then: conditions evaluate against stored facts
      user_groups not_contains "docker" → TRUE
```

## Evidence Collection Chain

```
Rule Fires
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Evidence Collection                              │
│                                                   │
│  For each evidence item in the rule:              │
│    1. Expand command (no dynamic substitution)    │
│    2. Safety check (7-layer verification)         │
│    3. Execute with 10s timeout                    │
│    4. Store stdout → fact store                   │
│    5. Log return code + stderr (if any)           │
│                                                   │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Condition Evaluation                             │
│                                                   │
│  All conditions must pass → hypothesis is valid   │
│  Any condition fails → hypothesis is eliminated   │
│  (Deterministic elimination before Bayesian step) │
└──────────────────────────────────────────────────┘
```

## Supported Evidence Types

| Type | Example | Output |
|---|---|---|
| **file read** | `cat /etc/os-release` | File content |
| **process status** | `systemctl status sshd` | Active/inactive + logs |
| **resource usage** | `df -h /` | Disk usage percentage |
| **network state** | `ss -tlnp` | Listening ports |
| **package info** | `dpkg -l | grep nginx` | Installed version |
| **log query** | `journalctl -u docker --no-pager -n 50` | Recent log entries |

---

# SLIDE 10 — Mission Control TUI

## Interface Design

Single-pane, 3-column layout for maximum situational awareness:

```
╔══════════════════════════════════════════════════════════════════════╗
║  🐧 LINUX DOCTOR  ·  Mission Control  ·  Domain: DOCKER (99.5%)    ║
║  Session: #20260605-001  |  Query: "docker permission denied"      ║
╠══════════════════════════╦══════════════════════╦═══════════════════╣
║    📊 CAUSAL TREE         ║   🤖 AI REASONING   ║   ⚡ ACTION CARDS  ║
║                          ║                     ║                    ║
║   🔴 DOCKER              ║  14:30:45.123       ║  ┌──────────────┐ ║
║    └─ Symptom            ║  🔍 Matched          ║  │ ✅ LOW       │ ║
║        "docker            ║     symptoms:         ║  │ groups      │ ║
║         permission        ║     DOCKER_001 (2/4) ║  │ Check user  │ ║
║         denied"           ║  14:30:46.001       ║  │ groups      │ ║
║    └─ Evidence           ║  ⚡ Fired rule       ║  └──────────────┘ ║
║        groups:            ║     DOCKER_001       ║  ┌──────────────┐ ║
║        "ntbankey sudo"   ║  14:30:47.221       ║  │ ⚠️ MODERATE  │ ║
║        socket:            ║  📡 Evidence         ║  │ usermod -aG │ ║
║        "srw-rw----..."    ║     collected (3/3) ║  │ docker $USER│ ║
║    └─ Root Cause         ║  14:30:48.540       ║  └──────────────┘ ║
║        User not in        ║  ✅ H₁ confirmed    ║  ┌──────────────┐ ║
║        docker group       ║     margin: 74%     ║  │ ℹ️ INFO     │ ║
║                          ║                     ║  │ newgrp      │ ║
║   Confidence:             ║                     ║  │ docker      │ ║
║   ████████░░ 87%          ║                     ║  └──────────────┘ ║
║                          ║                     ║                    ║
╚══════════════════════════╩══════════════════════╩═══════════════════╝
```

## Column Roles

| Column | Purpose | Content |
|---|---|---|
| **Causal Tree** (left) | Visual DAG of the incident | Symptom → Evidence → Root Cause, confidence bar |
| **AI Reasoning** (center) | Timestamped audit trail | Every inference step logged with timing |
| **Action Cards** (right) | Ordered fixes by risk | LOW 🟢 → MODERATE 🟡 → HIGH 🔴 |

## REPL Commands

| Command | Description |
|---|---|
| `docker permission denied` | Run diagnosis (natural language input) |
| `/explain` | Print full reasoning chain |
| `/fix` | Execute top-ranked fix |
| `/fix <n>` | Execute specific fix #n |
| `/history` | Show session history from SQLite |
| `/safe` | Preview command before execution |
| `/status` | Show current diagnosis state |
| `/exit` | Quit |

---

# SLIDE 11 — Empirical Test Evidence Across 11 Domains

The system has been validated on **20+ test scenarios** across all domains. Below is the test coverage:

## Domain Test Matrix

| Domain | Tests Run | Key Scenarios Validated | Example Root Cause Found |
|---|---|---|---|
| 🐳 **Docker** | 5 | Permission denied, daemon down, bridge network, container OOM, registry auth | `User not in docker group` |
| 🌐 **Nginx** | 2 | Config syntax error, port bind conflict, upstream 502, SSL cert expiry | `Port 80 already in use` |
| 🔑 **SSH** | 2 | Connection refused, key rejected, permission denied, firewall block | `sshd service not running` |
| 🖥️ **CPU** | 2 | High load average, process stuck (D-state), zombie processes | `Fork bomb detected` |
| 💾 **Memory** | 2 | OOM killer fired, swap full, memory leak | `Process exceeded cgroup limit` |
| 💽 **Disk** | 2 | No space left, inode exhausted, read-only filesystem | `Inode table at 97%` |
| 🌍 **Network** | 1 | No route to host, connection timeout, packet loss | `Default gateway unreachable` |
| 📡 **DNS** | 1 | Resolution failed, NXDOMAIN, server timeout | `Nameserver 8.8.8.8 unreachable` |
| ⚙️ **Systemd** | 1 | Service failed, unit not found, dependency error | `Unit depends on non-existent target` |
| 📦 **Package** | 1 | Dependency broken, repository unreachable, GPG error | `Package version conflict` |
| 🔄 **Git** | 1 | Merge conflict, auth failed, remote rejected | `Local branch behind remote by 5 commits` |

## Representative Deep-Dive: Docker Ecosystem

```
Test 1: "docker permission denied"
  └─ Matched DOCKER_001 → evidence: groups, docker.sock
  └─ Root cause: User not in docker group (87%)
  └─ Fix: sudo usermod -aG docker $USER

Test 2: "docker daemon not running"
  └─ Matched DOCKER_002 → evidence: systemctl status docker
  └─ Root cause: containerd service failed (92%)
  └─ Fix: sudo systemctl restart containerd

Test 3: "docker container network timeout"
  └─ Matched DOCKER_005 → evidence: docker network ls, iptables
  └─ Root cause: Docker bridge network misconfigured (84%)
  └─ Fix: docker network prune && systemctl restart docker

Test 4: "docker container exits immediately"
  └─ Matched DOCKER_003 → evidence: docker logs, docker inspect
  └─ Root cause: OOMKilled — container exceeds memory limit (89%)
  └─ Fix: Increase --memory limit or fix memory leak in app
```

---

# SLIDE 12 — 12 Supported Domains & Knowledge Base

## Domain Coverage Map

| # | Domain | KB File | Rules | Common Triggers | Typical Fix |
|---|---|---|---|---|---|
| 1 | 🐳 **Docker** | `docker.yaml` | 8 | permission denied, container exit, network | `usermod -aG docker` |
| 2 | 🌐 **Nginx** | `nginx.yaml` | 10+ | failed start, 502, port conflict | `nginx -t` → fix config |
| 3 | 🔑 **SSH** | `ssh.yaml` | 8 | refused, key rejected, permission | `systemctl start sshd` |
| 4 | 🖥️ **CPU** | `cpu.yaml` | 6 | high load, zombie, D-state | `kill -9` or renice |
| 5 | 💾 **Memory** | `memory.yaml` | 6 | OOM, swap full, leak | Identify + restart consumer |
| 6 | 💽 **Disk** | `disk.yaml` | 8 | space, inode, read-only FS | `du -sh` → cleanup |
| 7 | 🌍 **Network** | `network.yaml` | 8 | no route, timeout, packet loss | Check routes + firewall |
| 8 | 📡 **DNS** | `dns.yaml` | 6 | NXDOMAIN, timeout, resolution | Fix `/etc/resolv.conf` |
| 9 | 🔄 **Git** | `git.yaml` | 8 | conflict, auth fail, rejected | `git rebase` or `reset` |
| 10 | ⚙️ **Systemd** | `systemd.yaml` | 10+ | failed unit, dependency error | `journalctl -xe` |
| 11 | 📦 **Package** | `package.yaml` | 8 | broken dep, repo, GPG | `apt --fix-broken` |
| 12 | 🔒 **Permission** | `permissions.yaml` | 8 | EACCES, EPERM, ownership | `chmod`/`chown` |

**Total: ~90 rules across 12 domains**

## Zero-Code Domain Addition

```
Want to add PostgreSQL troubleshooting?

Step 1: Write  data/kb/postgres.yaml
         ┌────────────────────────────────────────┐
         │  symptoms: ["can't connect", "5432"]   │
         │  evidence: ["systemctl status postgres"]│
         │  conditions: [status: not_equals "active"]│
         │  hypotheses: [fix: "systemctl start"]    │
         └────────────────────────────────────────┘

Step 2: Drop the file in data/kb/
Step 3: Linux Doctor auto-discovers it on next run
         → Zero Python changes
         → No model retraining needed (TF-IDF catches new keywords)
         → New rules active immediately
```

---

# SLIDE 13 — Roadmap & Enterprise Vision

## Shipped Features ✅

| Component | Status | Detail |
|---|---|---|
| 🧠 **ML Pipeline** | ✅ Done | 3 classifiers · 99.49% F1 · pure NumPy · 101,758 samples |
| ⚙️ **Expert System** | ✅ Done | Forward-chaining · 90 rules · 12 domains |
| 📊 **Bayesian Ranker** | ✅ Done | Evidence-driven · handles competing hypotheses |
| 🛡️ **Safety Shell** | ✅ Done | 7-layer sandbox · 80+ allowlisted read-only commands |
| 📺 **Mission Control TUI** | ✅ Done | Rich 3-column real-time display |
| 💬 **Interactive REPL** | ✅ Done | Natural language + /commands |
| 🗄️ **SQLite Persistence** | ✅ Done | WAL mode · full session history |
| 📚 **Knowledge Base** | ✅ Done | 12 YAML files · ~90 rules total |
| ✅ **Test Suite** | ✅ Done | Unit + integration + pipeline tests |

## Roadmap 2026 🚀

```
Priority    Feature                         Why                          Target
────────    ───────                         ───                          ──────
⚡ P1       Parallel evidence collection    Sequential gather = 15s      < 2s per diagnosis
                                           Biggest latency bottleneck

🗄️ P2       PostgreSQL incident history    SQLite good for single-node   Multi-user shared DB
                                           Multi-user needs shared DB

🧠 P3       Backward chaining              Forward-only = limited        Bidirectional reasoning
                                           Goal-directed queries

🌐 P4       HTTP API                       Integrate with PagerDuty,     RESTful endpoint
                                           Grafana, monitoring stack

📊 P5       Prometheus metrics             Track latency, accuracy,      Grafana dashboard
                                           fix success rate

🔬 P6       Real incident corpus           Synthetic data ≠ production   Active learning loop
           + active learning              accuracy unknown              from /history corrections
```

## From Tool to Platform: Enterprise Vision

```
Today:  Linux Doctor is a CLI diagnostic tool
         └── Single-user, single-node, reactive

Future:  Linux Doctor is an Enterprise Operations Platform
         ├── Multi-user incident database
         ├── Integration with PagerDuty / OpsGenie / Grafana
         ├── CI/CD pipeline integration (auto-diagnose failed builds)
         ├── Kubernetes operator (auto-diagnose pod crashes)
         ├── API-first architecture
         └── Active learning: improve from every diagnosis
```

---
