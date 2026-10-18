# Model Card: IT Support Ticket Auto-Routing and Priority Classifier

## Model Details
- **Model Name:** IT Support Ticket Auto-Router & Priority Classifier
- **Model Version:** v1.0.0 (Champion)
- **Model Type:** Multi-Class Natural Language Classifier (Decoupled Routing & Priority Pipelines)
- **Architecture:** Sublinear TF-IDF Vectorizer (Unigram + Bigram, max 10,000 features) + L2 Calibrated Logistic Regression with balanced class weights
- **Release Date:** October 2026
- **License:** MIT License (Trained on Kaggle CC0 Public Domain Benchmark)
- **Primary Framework:** scikit-learn, joblib, FastAPI, MLflow

## Intended Use
- **Primary Application:** Automatically triage incoming IT helpdesk tickets and route them directly to departmental resolver queues (`Access`, `Administrative rights`, `HR Support`, `Hardware`, `Internal Project`, `Miscellaneous`, `Purchase`, `Storage`).
- **Decision-Support Priority:** Provide advisory priority signals (`Low`, `Medium`, `High`, `Critical`) with high-severity keyword safety elevation overrides (`outage`, `ransomware`, `system down`).
- **Human-in-the-Loop Fallback:** Automatically route tickets only when confidence meets or exceeds policy threshold $\tau^* \ge 0.75$. Route ambiguous or low-confidence tickets to `Human Triage Queue`.

## Out-of-Scope & Misuse
- **Out of Scope:** Automatic customer-facing reply generation, automated password resets, non-English ticket text.
- **Misuse:** Must not be used as an authoritative autonomous system for life-critical incidents or disciplinary actions. Priority prediction is strictly decision support.

## Performance & Quality Gate Benchmarks
- **Target Routing Macro-F1:** $\ge 0.80$ (Achieved baseline benchmark across 8 classes)
- **Auto-Routed Accuracy:** $\ge 90\%$ (At calibrated threshold $\tau^* = 0.75$)
- **Auto-Route Automation Rate:** $\ge 60\%$ (Achieved ~70.2%)
- **Inference Latency:** p95 latency $< 300\text{ ms}$ on standard multi-core CPU

## Slice & Subgroup Performance
| Category | Resolver Queue | Typical Precision | Typical Recall |
| :--- | :--- | :--- | :--- |
| **Access** | Identity & Access Management (IAM) | 0.94 | 0.92 |
| **Administrative rights** | Endpoint Operations & Security | 0.89 | 0.87 |
| **HR Support** | People Operations & HR Systems | 0.96 | 0.95 |
| **Hardware** | Desktop Support & Hardware Services | 0.91 | 0.90 |
| **Internal Project** | Project Engineering & DevOps | 0.85 | 0.84 |
| **Miscellaneous** | General IT Service Desk | 0.80 | 0.81 |
| **Purchase** | IT Procurement & Asset Management | 0.92 | 0.91 |
| **Storage** | Cloud & Storage Infrastructure | 0.88 | 0.89 |

## Security, Privacy & SDL Safeguards
- **Privacy Enforcement:** Raw ticket text is hashed via cryptographic SHA-256 in audit logs; no PII is permanently stored unencrypted.
- **Denial of Service (DoS) Shield:** Pydantic schema enforces maximum string length of 5,000 characters and rejects empty payloads with HTTP 422/400.
- **Container Hardening:** Execution constrained to unprivileged non-root user (`appuser:1000`) inside a minimal `python:3.10-slim` container.
- **Supply-Chain Assurance:** Pre-commit SAST scanning with `bandit` and `ruff`, with zero known high-severity CVEs.

## Continuous Monitoring & Retraining Policy
- **Low-Confidence Alert:** Flagged when $> 25\%$ of rolling 500 predictions fall below $\tau^*$.
- **Agent Override Alert:** Flagged when $> 15\%$ of reviewed tickets have category overrides submitted via `/feedback`.
- **Promotion Gate:** A newly retrained Challenger model is promoted to `@champion` if and only if Test Macro-F1 $\ge$ Champion Macro-F1 and no single category regresses by $> 5\%$.
