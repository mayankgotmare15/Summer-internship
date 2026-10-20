# IT Support Ticket Auto-Routing and Priority Classifier

Product Requirements Document and Implementation Plan | 1-Month MLOps Internship | Version 1.1 (Draft) | October 20, 2026

## 1. Executive Summary

IT service desks lose many agent hours reading, categorizing, and assigning incoming tickets. This project builds an end-to-end MLOps system that reads a ticket, predicts the team that should handle it and its priority, and routes it automatically when the model is confident. Uncertain tickets go to a human triage queue.

The deliverable is the full lifecycle around the model, not just the model: versioned data, reproducible training, experiment tracking, a containerized API, CI/CD, a demo UI, drift monitoring, and an automated retraining trigger. Everything is tied to one business outcome: agent hours saved per month.

Version 1.1 adds the people side of the service desk. Every ticket gets a named owner and a promised resolution time that the requester sees immediately, SLA-based escalation runs automatically, and requesters can escalate to a member they choose, with guardrails. Section 4A defines the roles and their work; Section 4B defines assignment, ETA, and escalation.

| Item | Summary |
| --- | --- |
| Product | Ticket Auto-Routing and Priority Classifier |
| Duration | 1 month (22 working days, 8 phases numbered 0 to 7) |
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
6. Give every ticket a named owner and a promised resolution time that the requester can see, and let requesters escalate to a person they choose.

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
| Owner and ETA shown to the requester | Workflow | Named assignee, team, and ETA shown within 5 seconds of ticket creation |
| SLA escalation ladder | Workflow | Fires at the configured points (first response, 50%, 75%, 100% of resolution time) in the simulated run |
| Requester-chosen escalation | Workflow | The chosen member is notified and responds, or the timeout fallback fires, in every test case |

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

## 4A. Roles, Responsibilities, and Work Assignment

Seven operating roles run the ticket flow, and the build is split into six delivery roles held by one intern and one mentor. Names and numbers below are demo data; replace them with the firm’s real roster and policies.

### 4A.1 Operating roles

| Role | Who | Assigned work | Authority |
| --- | --- | --- | --- |
| Requester (ticket raiser) | Any employee | Raises tickets, tracks status, assignee, and ETA, answers questions, confirms resolution, and can escalate (Section 4B) | Escalates own tickets; cannot change category or assignee directly |
| Service Desk Agent (L1 triager) | Service desk staff | Works the Human Review queue (low confidence, multi-issue, Miscellaneous); corrects category and priority; assigns the ticket; resolves simple requests such as password resets | Reassigns across teams; every correction is logged as model feedback |
| Resolver Engineer (L2) | Specialist in a resolver team | Works assigned tickets in their specialty, posts updates, keeps the ETA current, and resolves or hands back with a reason | Own assigned tickets only |
| Team Lead | Head of each resolver team | Balances workload, reassigns within the team, acts on SLA warnings, and handles escalations | Reassigns and re-prioritizes within the team |
| Approver | Requester’s line manager or the security owner | Approves access-sensitive or cost-bearing requests (admin rights, purchases) before work starts | Approves or rejects |
| Service Desk Manager and IT Delivery Manager (E3 and E4) | Service desk and delivery leadership | Own SLA compliance, take breached and top-level escalations, review the dashboard, and set SLA policy | Override any assignment; edit SLA policy |
| Platform Admin (MLOps) | The intern, with the mentor | Maintain the model, confidence threshold, routing map, roster, and SLA files; watch drift; run retraining | Configuration and deployment; does not work tickets |

### 4A.2 Resolver teams and the work assigned to each

The model’s category decides the team, and the roster decides the person. The mapping lives in routing\_map.yaml and can be changed without code.

| Ticket category | Resolver team | Specific work assigned | Example ticket |
| --- | --- | --- | --- |
| Access | Access and Identity Team | Password resets, account unlocks, VPN and application access, MFA problems | VPN keeps disconnecting |
| Administrative rights | Access and Identity Team, after Approver sign-off | Local admin rights and permission to install software | Need admin rights to install Python |
| Hardware | Desktop and Hardware Support | Laptop, monitor, keyboard, and printer faults; repairs and replacements | Laptop will not turn on |
| Storage | Storage and Infrastructure Team | Shared-drive quotas, backup restores, server and cloud disk space | Shared drive is full |
| HR Support | HR Systems Support | Payroll portal, leave system, and employee-data tool issues | Cannot update bank details |
| Purchase | Procurement and Asset Team, after Approver sign-off | Equipment and software requests, quotes, vendor orders, asset tags | Need a 27-inch monitor |
| Internal Project | Project and Application Support | Repository, environment, and tooling requests for internal projects | Repo access for a migration |
| Miscellaneous or low confidence | Service Desk (L1 triage) | Manual triage, then assignment to the right team | Outlook and printer problems in one ticket |

### 4A.3 Delivery roles (who builds what)

| Delivery role | Held by | Specific work | Phases |
| --- | --- | --- | --- |
| Project Owner and Reviewer | Mentor (also plays the Service Desk Manager) | Approves scope, targets, SLA values, and escalation rules; reviews each weekly checkpoint; grants tool and hosting access; judges the final demo | 0 to 7 |
| Data Engineer | Intern | Dataset ingestion with DVC, validation checks, splits, and the shared preprocessing module | 0 to 2 |
| ML Engineer | Intern | Baseline and comparison models, threshold sweep, evaluation, MLflow experiments and registry | 1 to 2 |
| Backend Engineer | Intern | FastAPI service, ticket store, roster, assignment engine, SLA and ETA calculator, notifications, and escalation endpoints | 3 to 4 |
| DevOps and MLOps Engineer | Intern | Docker, GitHub Actions CI/CD, deployment, Evidently monitoring, and the retraining workflow | 3, 5, and 6 |
| QA and Technical Writer | Intern | Unit, API, and workflow tests; sample tickets; README, model card, business report, and demo video | 2 to 7 |

## 4B. Assignment, ETA, and Escalation

Every ticket gets a named owner and a promised resolution time within seconds, and the requester can escalate to a person they choose. All values below are configurable defaults held in roster.yaml, sla.yaml, and escalation\_rules.yaml.

### 4B.1 What the requester sees

Right after raising a ticket, the requester gets a confirmation like this (sample data):

```
Ticket T-1042 received.
Category: Access          Priority: High
Assigned to: Priya Sharma, Access and Identity Team
First response by: today 3:30 PM
Expected resolution by: today 7:30 PM
Need it faster? Use Escalate to pick a person and give a reason.
```

The requester’s status page shows the same details plus the current status, escalation level, and an activity timeline, with an Escalate button. In the demo, notifications go to the in-app status page and to a simulated email log; a Slack or Teams webhook is optional.

| Event | Who is notified | What the message says |
| --- | --- | --- |
| Ticket created and assigned | Requester, assigned engineer | Ticket ID, category, priority, assignee, team, first-response time, and ETA |
| Sent to human review | Requester, service desk agents | Ticket is being reviewed; an owner will be named within 30 minutes |
| Work started or status changed | Requester | New status and any note from the engineer |
| ETA changed | Requester | New ETA and the reason |
| Reassigned | Requester, old and new engineer | New owner and ETA |
| SLA warning (75% of time used) | Assigned engineer, Team Lead | Time remaining |
| SLA breached | Team Lead, manager, requester | Breach notice, new committed ETA, and new contact |
| Escalated by requester | Chosen member, assignee, Team Lead | Reason, ticket summary, and response deadline |
| Resolved | Requester | Resolution note; confirm or reopen |

### 4B.2 How a named engineer is chosen

After the model (or an agent in Human Review) picks the team, the assignment engine picks the person:

1. Keep only team members who are on shift and not on leave.
2. Prefer members whose skill tags match the ticket, such as VPN or MFA for Access.
3. Among those, pick the one with the lowest open workload (weighted by priority) who is under their daily capacity.
4. Break ties by round robin.
5. If nobody qualifies, assign the Team Lead and flag the ticket.

Critical tickets go to the least-loaded available engineer and notify the Team Lead immediately. The roster file holds, for each member: name, email, team, role, skill tags, shift hours, daily capacity, leave dates, and an escalation-eligible flag.

### 4B.3 ETA and SLA targets

The ETA is a promise taken from the SLA policy, counted in business hours. The clock pauses while the ticket waits on the requester. For Administrative rights and Purchase tickets it starts only after approval (approval target: 1 business day).

| Priority | First response | Resolution target |
| --- | --- | --- |
| Critical | 15 minutes | 4 hours |
| High | 1 hour | 8 hours |
| Medium | 4 hours | 24 hours |
| Low | 8 hours | 72 hours |

These are placeholder defaults to confirm with the mentor. A later refinement (Could) adds the assignee’s open queue to the ETA, and a future version can predict resolution time from historical tickets instead of using fixed targets.

### 4B.4 Ticket lifecycle

```
New -> Triaged -> Assigned -> In progress -> Resolved -> Closed
       (auto-routed, or by an agent after Human Review)

Side states:
  Awaiting approval     before Assigned, for admin rights and purchases
  Waiting on requester  SLA clock paused; back to In progress on reply
  Escalated             a flag set from Assigned or In progress
  Reopened              Resolved -> In progress when the requester rejects the fix
```

### 4B.5 Automatic escalation ladder

Escalation levels are E1 assigned engineer, E2 Team Lead, E3 Service Desk Manager, and E4 IT Delivery Manager. The ladder runs on the clock:

1. Assignment: the engineer owns the ticket (E1). Critical tickets also notify the Team Lead at once.
2. First response missed: the ticket is reassigned to the next available engineer and the Team Lead is told.
3. 50% of resolution time used with no status update: reminder to the engineer.
4. 75% used: warning to the engineer and Team Lead; the Team Lead can reassign.
5. 100% used (SLA breach): escalates to the Service Desk Manager (E3); the requester is told about the breach and the new committed ETA.
6. Manager has not acted within 2 hours of a breach: escalates to the IT Delivery Manager (E4).

All thresholds are set in escalation\_rules.yaml, and every step is written to the audit log.

### 4B.6 Requester-chosen escalation

A requester can escalate any of their open tickets at any time and decides who receives it.

1. The requester clicks Escalate on the ticket page.
2. They choose a person from a searchable directory showing name, role, and team. The assignee’s Team Lead and the Service Desk Manager appear first as suggestions, but any listed member can be chosen.
3. They pick a reason (No response, Wrong team, Business-critical, Deadline at risk, Other) and write a short note. Both are required.
4. The system validates the request, then notifies the chosen member, the current assignee, and the Team Lead, and starts a response timer (2 business hours; 30 minutes for Critical).
5. The chosen member responds, or the timer decides:

```
Accept       -> chosen member becomes owner and posts a new ETA
Reassign     -> a named member becomes owner, with a new ETA
Decline      -> ticket returns to the Team Lead, with the reason
No response  -> escalation moves automatically to the chosen member’s manager
```

6. The requester is notified of the new owner and the new ETA at each step.

**Guardrails**

- A reason is mandatory, and every escalation is recorded in the audit log with who, when, why, and the outcome.
- At most 2 requester escalations per ticket per 24 hours, with a 1-hour cooldown between them (configurable).
- The current assignee and Team Lead are always notified, so nobody is bypassed silently.
- The chosen member must be active and escalation-eligible. If they are on leave, the system warns the requester and suggests their delegate.
- A requester cannot select themselves or the person who already owns the ticket.
- Escalating with the reason Wrong team is also logged as model feedback, so it counts toward the override rate used for drift monitoring and retraining.

## 5. Scope and Prioritization (MoSCoW)

| Priority | Items |
| --- | --- |
| Must | Data versioning, baseline routing model, MLflow tracking and registry, FastAPI service, Docker image, CI/CD, cloud deployment, drift monitoring, retraining trigger, README and business report |
| Should | Priority model, DistilBERT comparison, feedback endpoint, Streamlit UI with KPI dashboard, model card |
| Could | Rule-based priority overrides, batch prediction endpoint, Prometheus metrics, top-keyword explanations |
| Won’t (this release) | Live ticketing-system integration, response generation, multilingual support |

If time runs short, cut from the Could list first, then the bottom of the Should list. Never cut a Must.

**Added in version 1.1 (assignment, ETA, and escalation).** Must: named-engineer assignment, ETA shown to the requester, the SLA-based escalation ladder, requester-chosen escalation with guardrails, and the audit log. Should: approval step for admin rights and purchases, the SLA dashboard, and feeding Wrong team escalations to the model as feedback. Could: workload-adjusted ETA and Slack or Teams notifications. If time runs short, cut Could items first, then Should items.

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

**Additional functional requirements (version 1.1: assignment, ETA, and escalation)**

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-19 | Load a roster and directory from config (name, email, team, role, skills, shift, capacity, leave, escalation eligibility) | Must |
| FR-20 | After routing, assign a named engineer using availability, skill match, and workload; fall back to the Team Lead | Must |
| FR-21 | Compute first-response and resolution times from the SLA policy in business hours, with the clock paused while waiting on the requester | Must |
| FR-22 | Show the requester the assignee, team, and ETA right after ticket creation, and notify on every lifecycle event | Must |
| FR-23 | Provide a requester status page with status, assignee, ETA, escalation level, and activity timeline | Must |
| FR-24 | Run the automatic escalation ladder (first-response miss, 50%, 75%, and 100% of resolution time, manager timeout) | Must |
| FR-25 | Let the requester escalate to any eligible directory member, with a mandatory reason and note | Must |
| FR-26 | Enforce escalation guardrails: rate limit, cooldown, no self or current owner, active target, and notices to the assignee and Team Lead | Must |
| FR-27 | Let the chosen member accept, reassign, or decline, and move the escalation to their manager on timeout | Must |
| FR-28 | Keep an audit log of assignments, ETA changes, escalations, and outcomes | Must |
| FR-29 | Log escalations with the reason Wrong team as model feedback | Should |
| FR-30 | Add an approval step for Administrative rights and Purchase tickets, with the SLA clock starting after approval | Should |
| FR-31 | Show SLA compliance, escalation rate, mean time to first response, and workload per engineer on the dashboard | Should |
| FR-32 | Adjust the ETA using the assignee’s open queue | Could |
| FR-33 | Send notifications to a Slack or Teams webhook in addition to in-app and email | Could |

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

**Added components (version 1.1)**

| Component | Technology |
| --- | --- |
| Ticket store and audit log | SQLite (PostgreSQL optional) |
| Roster and directory | YAML configuration loaded at startup (roster.yaml) |
| Assignment engine | Python module implementing the rules in Section 4B.2 |
| SLA and escalation scheduler | APScheduler job in the API container, checking every minute; SLA state is derived from timestamps so a sleeping free-tier host catches up on wake |
| Notification service | In-app notifications and an SMTP test server or log-only email; optional Slack or Teams webhook |

### API summary

| Endpoint | Purpose |
| --- | --- |
| POST /predict | Input: text and an optional ticket\_id. Output: category, category confidence, priority, priority confidence, decision, routed team, model version |
| POST /predict/batch | The same, for a list of tickets (Could) |
| POST /feedback | Input: ticket\_id, predicted category, corrected category |
| GET /health | Liveness check |
| GET /model-info | Active model version, metrics, and threshold |

**Additional endpoints (version 1.1).** /predict stays the model-only endpoint; /tickets wraps it with assignment and ETA.

| Endpoint | Purpose |
| --- | --- |
| POST /tickets | Create a ticket; runs routing, assignment, and ETA; returns the requester view (assignee, team, ETA) |
| GET /tickets/{id} | Status, assignee, ETA, activity timeline, and escalation level |
| POST /tickets/{id}/status | Engineer updates the status or ETA, with a reason |
| POST /tickets/{id}/reassign | Agent or Team Lead reassigns the ticket |
| POST /tickets/{id}/escalate | Requester escalates to a chosen member with a reason |
| POST /escalations/{id}/respond | Chosen member accepts, reassigns, or declines |
| GET /directory/members | Searchable list of escalation-eligible members |
| GET /roster/workload | Open tickets per engineer, used by assignment and the dashboard |

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

**New modules (version 1.1).** `src/workflow/` holds assignment.py, sla.py, escalation.py, and notifications.py. `configs/` gains roster.yaml, sla.yaml, and escalation\_rules.yaml. `tests/` gains workflow tests that use a fake clock.

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
| Agent override rate | Feedback log | Over 15% of reviewed tickets (agent corrections plus escalations marked Wrong team) |
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

**Dashboard KPIs:** auto-route rate, accuracy on reviewed tickets, override rate, average confidence, tickets per category, SLA compliance, escalation rate, mean time to first response, and cumulative hours saved.

## 13. Implementation Plan (Phase-wise)

| Phase | Days | Theme | Main outcome |
| --- | --- | --- | --- |
| 0 | 1–2 | Setup and planning | Repo, tools, environment, and scope agreed |
| 1 | 3–5 | Data, EDA, baseline | Validated data and a baseline model |
| 2 | 6–9 | Training pipeline and tracking | Reproducible DVC pipeline, MLflow, quality gate |
| 3 | 10–12 | Serving, container, UI | Dockerized API and Streamlit demo |
| 4 | 13–16 | Ticket workflow, assignment, and escalation | Named owner, ETA, notifications, and escalation |
| 5 | 17–18 | CI/CD and deployment | Automated checks and a live deployment |
| 6 | 19–21 | Monitoring and retraining | Drift drill with automated retraining |
| 7 | 22 | Business report and final demo | Report, README, and demo video |

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

### Phase 3: Serving, Containerization, and UI (Days 10–12)

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

### Phase 4: Ticket Workflow, Assignment, ETA, and Escalation (Days 13–16)

**Objective.** Give every ticket a named owner, a promised time, and an escalation path (Sections 4A and 4B).

**Tasks**

- Create the sample roster and directory (roster.yaml): about 15 members across the resolver teams, with skills, shifts, capacity, leave dates, and escalation eligibility.
- Write sla.yaml and escalation\_rules.yaml with the priority targets, ladder thresholds, and guardrails.
- Build the ticket store (SQLite), the lifecycle states, and the audit log.
- Implement the assignment engine and the ETA calculator with business hours and clock pause.
- Build the notification service (in-app and simulated email) for every event in Section 4B.1.
- Implement the SLA scheduler: first-response reassignment, 50% reminder, 75% warning, breach escalation, and manager timeout.
- Implement requester-chosen escalation: directory search, validation and guardrails, accept, reassign, and decline responses, and the timeout fallback.
- Log Wrong team escalations as model feedback.
- Extend the Streamlit UI with a requester status page (assignee, ETA, Escalate button), an engineer queue, and a Team Lead view.
- Write tests for assignment rules, ETA math, ladder timing, and escalation guardrails, using a fake clock.

**Deliverables.** Ticket workflow service, extended UI, and workflow test suite.

**Exit criteria.** A new ticket shows the requester a named assignee and ETA; a simulated overdue ticket climbs the ladder; a custom escalation is accepted and recorded in the audit log.

### Phase 5: CI/CD and Deployment (Days 17–18)

**Objective.** Automate checks and releases.

**Tasks**

- Write ci.yml: ruff, pytest, data validation, smoke-train, and the quality gate.
- Write cd.yml: build the image, run a container smoke test, push to the registry, and deploy.
- Keep secrets in GitHub Secrets and protect the main branch.
- Deploy to the chosen host and verify /health and /predict on the live URL.
- Add a status badge and deployment notes to the README.

**Deliverables.** Green CI, automated deployment, and a public demo URL.

**Exit criteria.** A pull request changes code, CI passes, and merging it deploys automatically.

### Phase 6: Monitoring and Retraining (Days 19–21)

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

### Phase 7: Business Report, Documentation, and Demo (Day 22)

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
| Escalation misuse or spam | Alert fatigue and a bypassed process | Mandatory reason, rate limit and cooldown, notices to the assignee and Team Lead, and an audit log |
| Unrealistic or missed ETAs | Requesters lose trust | Base ETAs on the SLA policy, pause the clock while waiting on the requester, and announce every ETA change |
| Timers stop when a free-tier host sleeps | Missed escalations | Derive SLA state from timestamps, run a scheduled check, and document wake-up behavior |
| Invented roster and SLA data | Results look unrealistic | Label them as sample data, keep them in config files, and confirm values with the mentor |
| Added workflow scope | Phases 4 and 5 overrun | Phase 4 has its own 4 days; apply the cut line in Section 5 (Could items first, then Should) |

## 16. Timeline and Weekly Checkpoints

| Week | Days | Phases | Checkpoint demo |
| --- | --- | --- | --- |
| 1 | 1–5 | 0 and 1 | Repo, EDA findings, and baseline numbers |
| 2 | 6–10 | 2 and the start of 3 | MLflow comparison and a reproducible pipeline |
| 3 | 11–15 | 3 and 4 | Local API and demo UI; assignment and ETA working |
| 4 | 16–20 | End of 4, then 5, and the start of 6 | Escalation flows, CI/CD, and live deployment |
| 5 (short) | 21–22 | End of 6, then 7 | Drift drill and final presentation |

## 17. Definition of Done

- Data and models are versioned, and `dvc repro` works from a fresh clone.
- MLflow shows at least 8 runs and a registered champion model.
- Routing macro-F1 and auto-route accuracy meet the targets, or the gap is honestly explained.
- The Docker image runs locally and in the cloud, and the live /predict URL works.
- CI runs on every pull request and CD deploys on merge.
- A monitoring report is generated, and the drift drill triggers retraining and promotion.
- The Streamlit demo shows routing, human review, feedback, and KPIs.
- A new ticket shows the requester a named assignee, team, and ETA within seconds.
- The simulated SLA run triggers each step of the escalation ladder, and every step appears in the audit log.
- A requester can escalate to a chosen member, who can accept, reassign, or decline, and the timeout fallback works.
- README, model card, business report, and demo video are complete.

## 18. Open Questions

- Which deployment host will the firm or college allow?
- Are the dataset’s 8 categories close enough to the firm’s real teams, or should the routing map be adjusted?
- Is there an agreed value for triage minutes per ticket and for agent hourly cost in the business model?
- Should priority be a hard routing input or advisory only?
- Which notification channel will the firm use: email, Slack, or Microsoft Teams?
- Can requesters escalate to anyone in the company, or only to roster members flagged as escalation-eligible?
- What are the real SLA targets, business hours, and time zone? The values in Section 4B.3 are placeholders.
- Who approves admin-rights and purchase requests?

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

* **Escalation:** raising a ticket to a different or more senior person, either automatically when an SLA is at risk or by the requester’s choice.
* **ETA:** the expected resolution time promised to the requester, taken from the SLA policy.
* **E1 to E4:** escalation levels: assigned engineer, Team Lead, Service Desk Manager, and IT Delivery Manager. L1 and L2 are support tiers: service desk triage and resolver specialists.
* **Audit log:** the record of who assigned, changed, or escalated a ticket, when, and why.
