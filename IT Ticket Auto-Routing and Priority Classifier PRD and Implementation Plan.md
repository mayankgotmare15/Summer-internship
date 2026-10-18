# IT Support Ticket Auto-Routing and Priority Classifier

Product Requirements Document and Implementation Plan | 1-Month MLOps Internship | Version 1.0 (Draft) | October 18, 2026

## 1. Executive Summary

IT service desks lose many agent hours reading, categorizing, and assigning incoming tickets. This project builds an end-to-end MLOps system that reads a ticket, predicts the team that should handle it and its priority, and routes it automatically when the model is confident. Uncertain tickets go to a human triage queue.

The deliverable is the full lifecycle around the model, not just the model: versioned data, reproducible training, experiment tracking, a containerized API, CI/CD, a demo UI, drift monitoring, and an automated retraining trigger. Everything is tied to one business outcome: agent hours saved per month.

| Item | Summary |
| --- | --- |
| Product | Ticket Auto-Routing and Priority Classifier |
| Duration | 1 month (20 working days, 7 phases numbered 0 to 6) |
| Team | 1 intern, 1 mentor or reviewer |
| Core outcome | Percentage of tickets auto-routed correctly; agent hours saved per month |
| Budget | Free and open-source tools, free-tier hosting only |

## 2. Background and Problem Statement

**Current state.** Tickets arrive by email, portal, or chat into a shared queue. A triage agent reads each ticket, picks a category, assigns it to a resolver team, and sets a priority. This takes a few minutes per ticket.

**Pain points**

- Manual triage consumes agent hours that could go to resolving issues.
- Misrouted tickets bounce between teams, which increases resolution time and risks SLA breaches.
- Priority is set inconsistently between agents, so urgent tickets can wait.
- Triage quality drops during peak load and shift changes.

**Opportunity.** Ticket text carries enough signal to predict the right queue for most tickets. Automating the confident cases frees agents and speeds up first response, while a human fallback protects quality.

## 3. Goals, Non-Goals, and Success Metrics

### 3.1 Goals

1. Predict ticket category (the routing queue) from free text with high macro-F1.
2. Predict ticket priority (Low, Medium, High, Critical) as a decision-support signal.
3. Auto-route only confident predictions and escalate the rest to humans.
4. Deliver a reproducible, automated, and monitored MLOps pipeline.
5. Quantify business impact in agent hours and cost saved.

### 3.2 Non-Goals

- Integration with live ServiceNow, Jira, or Zendesk (the project uses a mock queue and documents the integration approach).
- Automatic ticket resolution or response generation.
- Multi-language support (English only).
- Heavy infrastructure such as Kubernetes or paid cloud services.
- Use of real customer data.

### 3.3 Success Metrics

Targets are initial and will be revisited with the mentor after the Phase 1 baseline.

| Metric | Type | Initial target |
| --- | --- | --- |
| Routing macro-F1 (test set) | Model | ≥ 0.80 |
| Routing accuracy on auto-routed tickets | Business | ≥ 90% |
| Auto-route rate | Business | ≥ 60% of tickets |
| Priority weighted-F1 | Model | Beat the majority-class baseline; report honestly |
| Net agent hours saved per month (modelled) | Business | Reported using the formula in Section 12 |
| API latency (p95, single prediction) | System | Under 300 ms |
| Reproducibility | MLOps | `dvc repro` reproduces results end to end |
| Pipeline automation | MLOps | CI on every pull request; CD on every merge to main |
| Drift response | MLOps | Simulated drift triggers an alert and a retraining run |

## 4. Users and Use Cases

| Persona | Need |
| --- | --- |
| Service desk agent (triager) | Fewer tickets to read, and a clear signal when a ticket needs human review |
| Resolver team lead | Tickets arrive in the right queue with a sensible priority |
| IT delivery manager | Visibility into automation rate, accuracy, and hours saved |
| ML or MLOps engineer (the intern) | Reproducible training, safe deployment, and early warning of model decay |

**User stories**

- As a triage agent, I want confident tickets routed automatically so that I only review the ambiguous ones.
- As a team lead, I want to see the predicted priority and confidence so that I can trust or override it.
- As a manager, I want a dashboard of auto-route rate, accuracy, and hours saved so that I can justify the tool.
- As an ML engineer, I want alerts when ticket patterns change so that I can retrain before accuracy falls.
- As an agent, I want to correct a wrong prediction in one click so that the system can learn from it.

## 5. Scope and Prioritization (MoSCoW)

| Priority | Items |
| --- | --- |
| Must | Data versioning, baseline routing model, MLflow tracking and registry, FastAPI service, Docker image, CI/CD, cloud deployment, drift monitoring, retraining trigger, README and business report |
| Should | Priority model, DistilBERT comparison, feedback endpoint, Streamlit UI with KPI dashboard, model card |
| Could | Rule-based priority overrides, batch prediction endpoint, Prometheus metrics, top-keyword explanations |
| Won’t (this release) | Live ticketing-system integration, response generation, multilingual support |

If time runs short, cut from the Could list first, then the bottom of the Should list. Never cut a Must.

## 6. Data Requirements

### 6.1 Datasets

| Dataset | Used for | Notes |
| --- | --- | --- |
| IT Service Ticket Classification Dataset (Kaggle, CC0) | Routing model | About 47,800 tickets across 8 categories: Access, Administrative rights, HR Support, Hardware, Internal Project, Miscellaneous, Purchase, Storage. The text arrives preprocessed (stopwords removed, lemmatized). |
| Multilingual Customer Support Tickets (Kaggle) | Priority model, plus raw-text samples for testing | Filter to English. Expected fields include subject, body, queue, priority, and language. Verify the columns at ingestion. |

### 6.2 Data caveats to document

- The routing dataset is pre-processed, so the same normalization (lowercase, stopword removal, lemmatization) must be applied at inference time. Also test on raw human-written text and report the gap.
- Priority labels may be only weakly related to ticket text, especially if the data is synthetic. Report priority results honestly and do not tune to hide this.
- The two datasets come from different sources, so routing and priority are two independent models behind one API. State this limitation in the model card.
- Check licenses and data cards before use. Never commit raw data to Git; use DVC.

### 6.3 Splits and validation

- Stratified split: 70% train, 15% validation, 15% test, with a fixed random seed.
- Validation checks (pandera or pytest): required columns present, no empty text, labels belong to the expected set, duplicates removed, and no leakage between splits.
- Drift simulation data: hold back one category (for example Storage) from the initial training so that it can act as a new category later. Also prepare a second batch of tickets with shifted vocabulary.

## 7. Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-01 | Version raw and processed datasets with DVC and a remote storage | Must |
| FR-02 | Validate data schema, labels, and duplicates before training | Must |
| FR-03 | Use one shared preprocessing module for training and inference | Must |
| FR-04 | Train a routing classifier and log parameters, metrics, and artifacts to MLflow | Must |
| FR-05 | Train a priority classifier with the same tracking | Should |
| FR-06 | Produce evaluation outputs: macro-F1, per-class report, confusion matrix, threshold sweep | Must |
| FR-07 | Register models in MLflow and promote to “champion” only after passing a quality gate | Must |
| FR-08 | Serve POST /predict returning category, priority, confidences, decision, routed team, and model version | Must |
| FR-09 | Apply a configurable confidence threshold: auto\_route above it, human\_review below it, changeable without code changes | Must |
| FR-10 | Map each category to a resolver team through a config file | Must |
| FR-11 | Log every prediction (timestamp, text hash, outputs, model version) | Must |
| FR-12 | Serve POST /feedback to record an agent’s corrected category | Should |
| FR-13 | Provide a Streamlit UI: paste a ticket, see the result, mock queues, and a KPI dashboard | Should |
| FR-14 | Run lint, tests, and a model quality gate in CI on every pull request | Must |
| FR-15 | Build and push the Docker image and deploy on merge to main | Must |
| FR-16 | Run scheduled monitoring of drift, low-confidence rate, and override rate, and publish an HTML report | Must |
| FR-17 | Trigger retraining when thresholds are breached, with champion-challenger promotion | Must |
| FR-18 | Provide README, architecture diagram, model card, and business report | Must |

## 8. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Performance | p95 latency under 300 ms for the baseline model on CPU; a batch of 100 tickets in under 5 seconds |
| Reproducibility | Fixed seeds, pinned dependencies, DVC pipeline stages, and an MLflow run for every training |
| Reliability | A /health endpoint; clear errors for empty or oversized text (limit 5,000 characters) |
| Portability | One Docker image runs locally and in the cloud with the same configuration |
| Security and privacy | No secrets in the repo (use GitHub Secrets and environment variables); log a hash or truncated text; use public data only |
| Maintainability | Modular code, type hints, ruff linting, and at least 70% test coverage on core modules |
| Cost | Free or open-source tooling and free-tier hosting only |
| Observability | Structured logs and a monitoring report archived for every run |

## 9. ML Design

### 9.1 Routing model

- Baseline: TF-IDF (unigrams and bigrams) with Logistic Regression and class weights.
- Comparisons: Linear SVM and, optionally, a fine-tuned DistilBERT.
- Selection criteria: macro-F1 first, then latency and model size.
- Confidence: predicted probability (calibrate the SVM with CalibratedClassifierCV).

### 9.2 Priority model

- The same TF-IDF approach on the priority dataset, with classes Low, Medium, High (and Critical if present).
- Treated as decision support. If accuracy is weak, the UI shows priority as a suggestion, and rule-based keyword overrides (for example outage, security breach, all users) can raise it.

### 9.3 Decision logic

```
prediction = routing_model(text)
if confidence >= THRESHOLD:  decision = auto_route    -> team = ROUTING_MAP[category]
else:                        decision = human_review  -> team = Triage Queue
```

The threshold is chosen from a validation-set sweep using the cost-benefit formula in Section 12: the value with the highest net hours saved while routing accuracy on auto-routed tickets stays at or above 90%.

### 9.4 Evaluation

- Metrics: macro-F1, weighted-F1, per-class precision and recall, and a confusion matrix.
- Slice analysis: rare categories and very short tickets.
- Robustness test: 30 hand-written, messy tickets (typos, long text, multiple issues), reported separately from the dataset test set.
- Model quality gate: a minimum macro-F1, and no per-class F1 drop of more than 5 points versus the current champion.

## 10. System Architecture

```
TRAINING:  Raw data -> DVC -> validate -> preprocess -> train -> evaluate -> MLflow registry (champion)

SERVING:   Ticket (UI or API) -> FastAPI /predict -> preprocess -> model -> decision logic
                                                                      |-> auto_route   -> resolver team queue
                                                                      |-> human_review -> triage queue

FEEDBACK:  prediction log + agent corrections -> Evidently monitoring (scheduled)
           -> alert -> retrain workflow -> challenger model -> promote if better -> redeploy
```

### Components

| Component | Technology |
| --- | --- |
| Source control | Git and GitHub |
| Data versioning and pipeline | DVC |
| Experiment tracking and registry | MLflow (local server via docker-compose, SQLite backend) |
| Modeling | scikit-learn; optional Hugging Face Transformers (DistilBERT) |
| Serving | FastAPI, Uvicorn, Pydantic |
| Containers | Docker and GitHub Container Registry |
| CI/CD | GitHub Actions |
| Monitoring | Evidently AI |
| Demo UI | Streamlit |
| Hosting | Render, Hugging Face Spaces (Docker), or an AWS or GCP free tier (check current free-tier limits) |
| Quality | pytest, ruff, pandera |

### API summary

| Endpoint | Purpose |
| --- | --- |
| POST /predict | Input: text and an optional ticket\_id. Output: category, category confidence, priority, priority confidence, decision, routed team, model version |
| POST /predict/batch | The same, for a list of tickets (Could) |
| POST /feedback | Input: ticket\_id, predicted category, corrected category |
| GET /health | Liveness check |
| GET /model-info | Active model version, metrics, and threshold |

### Repository structure

```
ticket-router/
  data/                 raw and processed data (DVC-tracked)
  src/
    data/               ingest.py, validate.py
    features/           preprocess.py
    models/             train.py, evaluate.py, register.py
    serving/            app.py, schemas.py, decision.py
    monitoring/         drift_report.py, check_thresholds.py
  configs/              params.yaml, routing_map.yaml
  tests/
  ui/                   streamlit_app.py
  .github/workflows/    ci.yml, cd.yml, monitor.yml, retrain.yml
  dvc.yaml  Dockerfile  docker-compose.yml  requirements.txt
  README.md  MODEL_CARD.md
```

## 11. MLOps Requirements

### 11.1 Experiment tracking and registry

Every run logs its parameters (vectorizer settings, regularization, class weights), metrics, confusion matrix, and the model itself. Models are registered and receive the “champion” alias only after passing the quality gate.

### 11.2 CI/CD workflows

| Workflow | Trigger | Steps |
| --- | --- | --- |
| ci.yml | Pull request | Install, ruff, pytest, data validation, smoke-train on a small sample, model quality gate |
| cd.yml | Merge to main | Build image, container smoke test, push to registry, deploy, call /health |
| monitor.yml | Weekly schedule and manual | Run drift and threshold checks, upload the report, open a GitHub issue if a threshold is breached |
| retrain.yml | Manual or triggered by monitoring | Pull the latest data, train a challenger, compare with the champion, promote if better, redeploy |

### 11.3 Monitoring and retraining trigger

A classifier cannot predict a category it has never seen. The system therefore detects the symptoms of change and retrains once new labeled data is available.

| Signal | Source | Example threshold |
| --- | --- | --- |
| Low-confidence rate | Prediction log | Over 25% of the last 500 tickets (compare with the baseline measured on test data) |
| Text or data drift | Evidently on TF-IDF or embedding features | Drift flagged on a significant share of features |
| Agent override rate | Feedback log | Over 15% of reviewed tickets |
| Prediction distribution shift | Evidently | Category mix changes beyond a set limit |

**Retraining policy.** When any threshold is breached, an alert is raised. New labeled tickets (from feedback or a new batch) are added through DVC and the pipeline trains a challenger. It is promoted only if its macro-F1 is at least equal to the champion’s and no class regresses by more than 5 points.

## 12. Business Impact Model

**Definitions:** N = tickets per month; a = auto-route rate; p = routing accuracy on auto-routed tickets; t = minutes of manual triage saved per ticket; c = extra minutes caused by a misrouted ticket (re-triage and delay); r = loaded cost per agent hour.

- Net minutes saved per month = N × a × \[ t − (1 − p) × c \]
- Net cost saved = (net minutes ÷ 60) × r

Illustrative assumptions (replace them with your own and label them as assumptions):

| Input | Value |
| --- | --- |
| N | 5,000 tickets per month |
| a | 70% |
| p | 92% |
| t | 3 minutes |
| c | 15 minutes |
| r | 10 USD per hour |

**Result:** 5,000 × 0.70 × \[3 − 0.08 × 15\] = 3,500 × 1.8 = 6,300 minutes, which is 105 hours per month, or about 1,050 USD per month. Ignoring the misroute penalty would give 175 hours and overstate the benefit.

**Threshold sweep.** For thresholds from 0.50 to 0.95, plot a, p, and net hours saved, then choose the best threshold subject to p ≥ 90%. Include this chart in the business report.

**Dashboard KPIs:** auto-route rate, accuracy on reviewed tickets, override rate, average confidence, tickets per category, and cumulative hours saved.

## 13. Implementation Plan (Phase-wise)

| Phase | Days | Theme | Main outcome |
| --- | --- | --- | --- |
| 0 | 1–2 | Setup and planning | Repo, tools, environment, and scope agreed |
| 1 | 3–5 | Data, EDA, baseline | Validated data and a baseline model |
| 2 | 6–9 | Training pipeline and tracking | Reproducible DVC pipeline, MLflow, quality gate |
| 3 | 10–13 | Serving, container, UI | Dockerized API and Streamlit demo |
| 4 | 14–16 | CI/CD and deployment | Automated checks and a live deployment |
| 5 | 17–19 | Monitoring and retraining | Drift drill with automated retraining |
| 6 | 20 | Business report and final demo | Report, README, and demo video |

### Phase 0: Setup and Planning (Days 1–2)

**Objective.** A clean foundation and a shared understanding of scope.

**Tasks**

- Review this PRD with the mentor; confirm scope, targets, and the deployment host.
- Create the GitHub repo with the structure from Section 10, a .gitignore, and a branching rule (feature branches, pull requests into main).
- Set up a Python environment with pinned requirements and pre-commit hooks for ruff.
- Initialize DVC and configure a remote storage (Google Drive, an S3-compatible bucket, or a similar free option).
- Start MLflow with docker-compose and confirm the UI opens.
- Download both datasets and read their data cards and licenses.

**Deliverables.** Repo skeleton, working tool chain, and signed-off scope.

**Exit criteria.** `dvc status`, the MLflow UI, and an empty CI run all work.

### Phase 1: Data, EDA, and Baseline Model (Days 3–5)

**Objective.** Understand the data and set a baseline to beat.

**Tasks**

- Ingest raw data under DVC; write ingest.py and validate.py (schema, labels, duplicates, empty text).
- Write an EDA notebook: class distribution, text length, top terms per class, label noise, duplicates, and the relationship between priority and text.
- Build preprocess.py as the single module shared by training and inference.
- Create stratified, seeded splits (70/15/15) and set aside the held-back category for the later drift drill.
- Train the TF-IDF plus Logistic Regression baseline and record macro-F1 and the per-class report.
- Write the first 30 hand-written messy test tickets (see Appendix A for examples).

**Deliverables.** EDA notebook, validated processed data tracked by DVC, and baseline metrics.

**Exit criteria.** Baseline macro-F1 is recorded and the PRD targets are reviewed with the mentor.

### Phase 2: Training Pipeline and Experiment Tracking (Days 6–9)

**Objective.** Make training reproducible and every experiment comparable.

**Tasks**

- Convert the steps into DVC stages: ingest, validate, preprocess, train, evaluate.
- Move all parameters into params.yaml and fix random seeds.
- Log runs to MLflow and run at least 8 experiments (vectorizer settings, regularization, class weights, Linear SVM, and optionally DistilBERT).
- Train the priority model and log it the same way.
- Generate evaluation artifacts: confusion matrix, per-class report, and the threshold sweep.
- Write register.py to register models and promote one to champion after the quality gate.
- Write unit tests for preprocessing, validation, and decision logic.

**Deliverables.** A `dvc repro` pipeline, an MLflow comparison table, a registered champion model, and the first tests.

**Exit criteria.** A fresh clone reproduces the champion’s metrics, and the chosen confidence threshold is documented with its justification.

### Phase 3: Serving, Containerization, and UI (Days 10–13)

**Objective.** Expose the model as a reliable service with a usable demo.

**Tasks**

- Build the FastAPI app with Pydantic schemas, model loading, and the decision logic.
- Implement /predict, /health, /model-info, and /feedback, and add prediction logging.
- Make the threshold and routing map configurable through environment variables and YAML.
- Write API tests with FastAPI TestClient covering valid, empty, oversized, and messy inputs.
- Write the Dockerfile (slim base image, non-root user) and a docker-compose file for the API and MLflow.
- Build the Streamlit UI: ticket box, result card, mock team queues, a human-review queue, a feedback button, and a KPI tab.

**Deliverables.** A Docker image that runs locally, the demo UI, and passing API tests.

**Exit criteria.** `docker compose up` gives a working end-to-end demo, and p95 latency has been measured and recorded.

### Phase 4: CI/CD and Deployment (Days 14–16)

**Objective.** Automate checks and releases.

**Tasks**

- Write ci.yml: ruff, pytest, data validation, smoke-train, and the quality gate.
- Write cd.yml: build the image, run a container smoke test, push to the registry, and deploy.
- Keep secrets in GitHub Secrets and protect the main branch.
- Deploy to the chosen host and verify /health and /predict on the live URL.
- Add a status badge and deployment notes to the README.

**Deliverables.** Green CI, automated deployment, and a public demo URL.

**Exit criteria.** A pull request changes code, CI passes, and merging it deploys automatically.

### Phase 5: Monitoring and Retraining (Days 17–19)

**Objective.** Detect model decay and respond automatically.

**Tasks**

- Build a traffic simulator that replays test tickets to the API in batches, including the shifted-vocabulary batch and the held-back category.
- Write drift\_report.py (Evidently) and check\_thresholds.py for low-confidence rate, drift, and override rate.
- Add monitor.yml (weekly and manual) that archives the HTML report and opens a GitHub issue on a breach.
- Add retrain.yml with champion-challenger logic and automated redeploy.
- Run the full drill: normal traffic, then drift, then alert, then retrain, then promotion, then recovered metrics.
- Record before and after numbers for the report.

**Deliverables.** Drift report, alert evidence, a retraining run in MLflow, and a before and after comparison.

**Exit criteria.** The drill runs end to end with no manual code changes.

### Phase 6: Business Report, Documentation, and Demo (Day 20)

**Objective.** Package the work for stakeholders.

**Tasks**

- Finalize the README with an architecture diagram, setup steps, and screenshots.
- Complete the model card: data, metrics, limitations, intended use, and retraining policy.
- Write the one-page business summary: problem, results, threshold choice, hours saved, and risks.
- Record a 3 to 5 minute demo video covering ticket in, routing, feedback, drift, and retrain.
- Present to the mentor and collect feedback.

**Deliverables.** Final repo, business report, demo video, and presentation.

**Exit criteria.** Every item in the Definition of Done (Section 17) is complete.

## 14. Testing Strategy

| Level | What is tested |
| --- | --- |
| Unit | Preprocessing, label mapping, decision logic, and threshold boundaries |
| Data | Schema, label set, duplicates, and leakage between splits |
| Model | Quality gate on a fixed test set, per-class regression check, and messy-ticket robustness |
| API | Valid and invalid inputs, error codes, response schema, and latency |
| Integration | Container smoke test in CI and a live /health check after deployment |
| Monitoring | The drill with simulated drift triggers the alert and the retraining workflow |

## 15. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Pre-processed dataset text differs from real tickets | Poor real-world accuracy | Shared preprocessing at inference, a messy-ticket test set, and reporting the gap |
| Priority labels weakly related to text | Low priority accuracy | Treat as decision support, report honestly, and add optional rule overrides |
| Class imbalance and rare categories | Low recall on small classes | Class weights, macro-F1, and per-class monitoring |
| Scope creep (for example DistilBERT) | Missed deadline | Follow the MoSCoW rules; attempt transformers only after all Must items are done |
| Free-tier limits or cold starts | Slow or unavailable demo | Keep the image small, document the wake-up time, and keep a local docker-compose fallback |
| Tool setup delays | Lost days | Do setup in Phase 0 and ask the mentor early |
| Time overrun | Incomplete deliverables | Weekly checkpoints; cut Could items first |

## 16. Timeline and Weekly Checkpoints

| Week | Phases | Checkpoint demo |
| --- | --- | --- |
| 1 | 0 and 1 | Repo, EDA findings, and baseline numbers |
| 2 | 2 and the start of 3 | MLflow comparison and a reproducible pipeline |
| 3 | 3 and 4 | Local and live API with CI/CD |
| 4 | 5 and 6 | Drift drill and final presentation |

## 17. Definition of Done

- Data and models are versioned, and `dvc repro` works from a fresh clone.
- MLflow shows at least 8 runs and a registered champion model.
- Routing macro-F1 and auto-route accuracy meet the targets, or the gap is honestly explained.
- The Docker image runs locally and in the cloud, and the live /predict URL works.
- CI runs on every pull request and CD deploys on merge.
- A monitoring report is generated, and the drift drill triggers retraining and promotion.
- The Streamlit demo shows routing, human review, feedback, and KPIs.
- README, model card, business report, and demo video are complete.

## 18. Open Questions

- Which deployment host will the firm or college allow?
- Are the dataset’s 8 categories close enough to the firm’s real teams, or should the routing map be adjusted?
- Is there an agreed value for triage minutes per ticket and for agent hourly cost in the business model?
- Should priority be a hard routing input or advisory only?

## 19. Future Enhancements

- Integrate with ServiceNow or Jira through webhooks.
- Add an embedding-based or fine-tuned transformer model with similar-ticket search.
- Show the top terms behind each prediction for explainability.
- Use active learning to send low-confidence tickets for labeling.
- Run challenger models in shadow or canary mode before promotion.
- Add multilingual support.

## Appendix A: Sample Messy Test Tickets

Expected labels are a starting guess; adjust them to the dataset’s own category definitions.

| Ticket text | Expected category | Expected decision |
| --- | --- | --- |
| pls give me admin rights on my laptop to install python | Administrative rights | auto\_route |
| laptop wont turn on after the update, screen black | Hardware | auto\_route |
| need a new 27 inch monitor for the new joiner | Purchase | auto\_route |
| shared drive full, cant save files since morning, whole team blocked | Storage | auto\_route, high priority |
| how do i update my bank details in the payroll portal | HR Support | auto\_route |
| password reset not working and account locked | Access | auto\_route |
| request access to the project repo for the migration work | Access or Internal Project | likely human\_review |
| outlook keeps asking password and my printer is also not working | Multiple issues | human\_review |

## Appendix B: Glossary

- **MLOps:** practices that automate and monitor the full lifecycle of a machine learning system.
- **DVC:** a tool that versions data and pipeline stages alongside Git.
- **MLflow:** a tool for experiment tracking and a model registry.
- **Champion and challenger:** the model currently in production and a newly trained candidate that must beat it before promotion.
- **Data drift:** a change in the incoming data compared with the training data.
- **Macro-F1:** the average F1 score across classes, giving rare classes equal weight.
- **SLA:** a service-level agreement, the response or resolution time promised to the client.
