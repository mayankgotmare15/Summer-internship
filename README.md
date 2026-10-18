# IT Support Ticket Auto-Routing and Priority Classifier
### Enterprise MLOps Pipeline & Secure Development Lifecycle (SDL) Implementation

[![CI Pipeline](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](#)
[![CD Pipeline](https://img.shields.io/badge/CD-Automated-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.10-blue.svg)](#)
[![Security Hardened](https://img.shields.io/badge/Security-SDL%20Hardened-success.svg)](#)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](#)

---

## 1. Executive Summary

IT service desks lose thousands of hours triaging, categorizing, and assigning incoming service requests. This repository contains an **end-to-end, production-grade MLOps system** that:
1. Ingests free-text IT support tickets.
2. Predicts the handling queue (`Access`, `Administrative rights`, `HR Support`, `Hardware`, `Internal Project`, `Miscellaneous`, `Purchase`, `Storage`).
3. Predicts ticket priority (`Low`, `Medium`, `High`, `Critical`) as an advisory signal with keyword safety overrides.
4. Automatically routes confident predictions ($\ge \tau^*$) while escalating ambiguous tickets to a human triage queue to avoid misrouting penalties.
5. Continuously monitors for feature and target drift using **Evidently AI**, triggering automated continuous retraining (CT) workflows upon threshold breach.

---

## 2. System Architecture

```
[ Incoming IT Ticket ]
         │
         ▼
┌─────────────────────────────────┐
│   FastAPI Service (:8000)       │
│  - Input Length Bounds (<5000c) │
│  - Non-Root Container Execution │
│  - Latency < 300 ms on CPU      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Shared Preprocessing Engine   │
│  (Tokenize / Lower / Lemmatize) │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Champion Calibrated Classifier │
│  (TF-IDF + Logistic Regression) │
└────────────────┬────────────────┘
                 │
                 ▼
         Confidence >= Tau?
         ├── YES ──► Auto-Route to Department Queue (Accuracy >= 90%)
         └── NO  ──► Escalate to Human Triage Queue (Fallback Safety)
                 │
                 ▼
┌─────────────────────────────────┐
│   Audit & Observability Log     │
│  - Anonymized Text SHA-256 Hash │
│  - Timestamp, Confidence, Class │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Evidently AI Monitoring Engine│
│  - Data & Concept Drift Alerts  │
│  - Low-Confidence Spikes (>25%) │
│  - Agent Override Rate (>15%)   │
└────────────────┬────────────────┘
                 │ (Breach Detected)
                 ▼
┌─────────────────────────────────┐
│ Continuous Retraining (CT) Loop │
│  - Train Challenger on New Data │
│  - Champion-Challenger Gate     │
│  - Automated Zero-Downtime CD   │
└─────────────────────────────────┘
```

---

## 3. Repository Structure

```
.
├── .github/workflows/
│   ├── ci.yml                 # Linting, security scanning, unit tests, model gate
│   ├── cd.yml                 # Docker build, container scan, GHCR push, deployment
│   ├── monitor.yml            # Scheduled drift analysis & threshold guard
│   └── retrain.yml            # Automated Continuous Retraining (CT) workflow
├── configs/
│   ├── params.yaml            # Hyperparameters, paths, and business constants
│   └── routing_map.yaml       # Department queue mappings and fallback queue
├── data/
│   ├── raw/                   # Raw ticket datasets (tracked via DVC)
│   ├── processed/             # Stratified splits (train, val, test, drift holdout)
│   └── monitoring/            # Production prediction and feedback audit logs
├── models/                    # Serialized Champion model artifacts
├── src/
│   ├── data/
│   │   ├── ingest.py          # Data ingestion & bootstrap generator
│   │   ├── split.py           # Stratified train/val/test splitting
│   │   └── validate.py        # Pandera data contract validation & leakage detection
│   ├── features/
│   │   └── preprocess.py      # Shared preprocessing (prevents train-serving skew)
│   ├── models/
│   │   ├── train.py           # Training pipeline with MLflow logging
│   │   ├── evaluate.py        # Evaluation & cost-benefit threshold sweep
│   │   └── register.py        # Model quality gate and champion promotion
│   ├── serving/
│   │   ├── app.py             # FastAPI REST microservice
│   │   ├── schemas.py         # Pydantic request/response data contracts
│   │   └── decision.py        # Confidence decision engine & keyword overrides
│   └── monitoring/
│       ├── drift_report.py    # Telemetry and Evidently drift reporting
│       ├── check_thresholds.py# Operational threshold breach checker
│       └── simulate_traffic.py# Synthetic production traffic simulator
├── tests/                     # Comprehensive pytest test suite
├── ui/
│   └── streamlit_app.py       # Multi-tab demonstration UI
├── Dockerfile                 # Hardened, non-root, multi-stage Dockerfile
├── docker-compose.yml         # Local orchestration (MLflow + API + UI)
├── requirements.txt           # Pinned production dependencies
├── pyproject.toml             # Ruff, Pytest, and Bandit configuration
├── MODEL_CARD.md              # Formal governance model card
└── README.md                  # System documentation
```

---

## 4. Quickstart Guide

### Option A: Local Python Environment
```bash
# 1. Clone repository
git clone https://github.com/your-org/ticket-router.git
cd ticket-router

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Ingest data, train champion model, and evaluate
python src/data/ingest.py
python src/data/split.py
python src/models/train.py
python src/models/evaluate.py
python src/models/register.py

# 5. Launch FastAPI microservice
uvicorn src.serving.app:app --host 0.0.0.0 --port 8000

# 6. Launch Streamlit Demo UI
streamlit run ui/streamlit_app.py
```

### Option B: Docker Compose (All Services)
Launch the API, Streamlit UI, and local MLflow tracking server with a single command:
```bash
docker compose up --build
```
- **Streamlit Demo UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MLflow Tracking Server:** [http://localhost:5000](http://localhost:5000)

---

## 5. Security Development Lifecycle (SDL) Controls

| SDL Stage | Security Implementation in this Project |
| :--- | :--- |
| **Governance** | Protected `main` branch, pre-commit hooks running `ruff` and `bandit` |
| **Privacy & Sanitization**| Raw text hashed via SHA-256 before logging; zero unredacted PII in production logs |
| **Data Contracts** | Pandera schema validation rejecting invalid classes and empty strings |
| **Denial of Service (DoS)**| Pydantic schema strictly bounding input text length to 5,000 characters |
| **Container Hardening** | Multi-stage Docker build executed under an unprivileged user (`appuser:1000`) |
| **Vulnerability Scanning**| Automated static analysis in CI with Bandit and container image scanning |

---

## 6. Business Impact & ROI Model

Net business savings are quantified using the formula:
$$\text{Net Minutes Saved per Month} = N \times a \times [t - (1 - p) \times c]$$

Where:
- $N = 5,000\text{ tickets/month}$
- $a = \text{Auto-route rate (e.g. } 70.2\%)$
- $p = \text{Routing accuracy on auto-routed tickets (e.g. } 92.4\%)$
- $t = 3\text{ minutes of manual triage saved per ticket}$
- $c = 15\text{ minutes misroute delay/re-triage penalty}$
- $r = \$10\text{ loaded cost per agent hour}$

**Baseline Impact:** ~105 net agent hours saved per month, translating to approximately **$1,050 USD / month** in net direct operational savings.
