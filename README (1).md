# Production Design: IT Ticket Auto-Routing and Priority Classifier

Companion to the PRD v1.1 and the frontend plan | Draft 1 | October 20, 2026

This folder takes the PRD to a production design: backend modules with their routers, controllers and services, the database, the ML services, end-to-end flows, and wireframes for both the frontend and the backend. All diagrams are Mermaid and render in the file preview and on GitHub.

**How "SDL" was read.** As system design plus SDLC practice: C4 context, container and component diagrams, sequence diagrams, state machines, data-flow diagram with trust boundaries, ERD, deployment view, STRIDE threat model, ADRs, CI/CD, test strategy and a requirement traceability matrix.

---

## Files, in reading order

| File | What it answers |
| --- | --- |
| [01-system-architecture.md](01-system-architecture.md) | Why a modular monolith and not microservices, C4 diagrams, deployment on free tier, environments, startup sequence |
| [02-backend-design.md](02-backend-design.md) | Layering (router, controller, service, repository), repo layout, 13 modules, all 54 endpoints with auth, schemas, error codes, the hard use cases in pseudocode, assignment engine, SLA ladder, RBAC, jobs, config |
| [03-database-design.md](03-database-design.md) | ERD, every table with constraints and indexes, KPI views, migrations, seeding, retention, concurrency guards |
| [04-ml-services.md](04-ml-services.md) | DVC pipeline stages, model bundle, MLflow registry, quality gate, inference engine and latency budget, degraded mode, monitoring signals, retraining and promotion, drift drill |
| [05-end-to-end-flows.md](05-end-to-end-flows.md) | Whole-system loop, 4 state machines, 10 sequence diagrams, data-flow diagram, failure-mode table |
| [06-wireframes.md](06-wireframes.md) | 14 frontend and 8 backend wireframes, each wired to its endpoints, modules and tables |
| [07-production-sdlc.md](07-production-sdlc.md) | SDLC process, CI/CD workflows, Dockerfile, secrets, observability and SLOs, STRIDE, test strategy, runbooks, build plan by phase with cut line, ADRs, FR traceability |
| [frontend-handoff.md](frontend-handoff.md) | What this design adds or changes for the frontend plan (owned by the frontend thread) |

---

## Key decisions at a glance

1. **Modular monolith, not microservices.** One FastAPI image with 13 bounded-context modules that only talk through service interfaces and domain events. Microservices would break three PRD constraints (free tier, no Kubernetes, one image). A split path is documented per module. Training, monitoring and retraining already run separately as GitHub Actions jobs.
2. **Postgres in production, SQLite in tests.** Free-tier hosts wipe local disk on redeploy, which would lose tickets and the prediction log that drift monitoring needs.
3. **Model baked into the image.** `models/champion.json` in Git points to the MLflow run; CD downloads and verifies the bundle. What is on `main` is what is live; rollback is a revert.
4. **Hosted MLflow (DagsHub free) as the default.** A local-only MLflow cannot be reached by GitHub Actions, so automated retraining would not work.
5. **SLA state derived from timestamps** with one idempotent tick that both the in-process scheduler and a 15-minute GitHub cron call. A sleeping host catches up and sends one combined notice.
6. **Transactional outbox.** Ticket, assignment, ETA, audit and notifications commit together; email goes out after commit with retries.
7. **No breaking.** A missing model never stops ticket intake (tickets go to human review), double submits are idempotent, ladder steps fire exactly once, and every escalation race has one winner. The full list is in 05 section 5.
8. **Promotion through an auto-merging PR**, so the mentor sees every model change with its metrics.

## Defaults picked where the PRD is open

These are assumptions, not decisions; confirm them with the mentor.

| Question | Default in this design |
| --- | --- |
| Hosting (PRD open question 1) | Render free web service + Neon Postgres + DagsHub + Streamlit Community Cloud |
| Business hours and timezone (open question 7) | Asia/Kolkata, Mon to Fri 09:00 to 18:00; Critical tickets on a 24x7 calendar |
| Priority as routing input (open question 4) | Advisory; rules can only raise it |
| Escalation targets (open question 6) | Escalation-eligible roster members only |
| Approvers (open question 8) | Line manager for admin rights and purchases, set per category |
| Reopen behaviour | SLA clock resumes from where it stopped |
| Auto-close | 3 business days after Resolved without a reply |
| First-response miss | One automatic reassignment, then Team Lead only |

## What changes for the frontend plan

Nothing in its design system, screens or routes. It gains 11 endpoints that its screens already imply, an `/api/v1` prefix, `allowed_actions` and `escalation_eligibility` fields, and one change to the Streamlit console: in production it saves config through admin endpoints instead of writing YAML files. Details in [frontend-handoff.md](frontend-handoff.md).
