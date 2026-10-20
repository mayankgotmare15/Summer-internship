# 05. End-to-End Flows

Part of the production design. Every flow below names the screen (frontend plan section 6), the endpoint and module (02), and the tables (03), so a change in one place can be traced through the others.

Contents: 1 Production flow overview · 2 State machines · 3 Sequence diagrams · 4 Data-flow diagram and trust boundaries · 5 Failure modes ("no breaking")

---

## 1. Production flow overview

The whole system as one loop: ticket in, routed, worked, measured, model improved, redeployed.

```mermaid
flowchart TB
  subgraph Intake
    A1[Requester describes problem<br/>/app/new] --> A2[POST /tickets]
    A2 --> A3{Model confident?}
  end
  subgraph Routing
    A3 -- yes --> B1[Auto-route to resolver team]
    A3 -- no --> B2[Human Review queue<br/>/desk/review]
    B2 --> B3[Agent corrects + assigns<br/>POST /tickets/id/triage]
    B3 --> FB1[(feedback row)]
    B1 --> B4{Needs approval?}
    B3 --> B4
    B4 -- yes --> B5[Approver decides<br/>/approvals]
    B4 -- no --> C1
    B5 -- approve --> C1
  end
  subgraph Work
    C1[Assignment engine names an engineer<br/>SLA clock starts, ETA shown] --> C2[Engineer works ticket<br/>/work]
    C2 --> C3{Resolved?}
    C3 -- no, clock running --> L1[SLA ladder:<br/>reassign, remind, warn, E3, E4]
    L1 --> C2
    C2 -. requester escalates .-> E1[Chosen member responds<br/>/escalations/id]
    E1 --> C2
    E1 -. reason wrong_team .-> FB1
    C3 -- yes --> C4[Requester confirms or reopens]
  end
  subgraph Learn
    P1[(predictions log)] --> M1[monitor.yml weekly]
    FB1 --> M1
    M1 --> M2{Threshold breached?}
    M2 -- yes --> R1[retrain.yml:<br/>feedback + data -> challenger]
    R1 --> R2{Quality gate}
    R2 -- pass --> R3[Promotion PR -> auto-merge]
    R3 --> D1[cd.yml builds image with new model<br/>and deploys]
    D1 --> A2
  end
  A2 --> P1
```

---

## 2. State machines

### 2.1 Ticket lifecycle (PRD 4B.4)

```mermaid
stateDiagram-v2
  [*] --> New: POST /tickets
  New --> Triaged: auto_route, or agent triage
  Triaged --> AwaitingApproval: category needs approval
  AwaitingApproval --> Assigned: approved, clock starts
  AwaitingApproval --> Resolved: rejected
  Triaged --> Assigned: engineer picked, clock starts
  Assigned --> InProgress: engineer starts work, first response met
  Assigned --> Assigned: reassign
  InProgress --> InProgress: reassign or ETA change
  Assigned --> WaitingOnRequester: request info, clock paused
  InProgress --> WaitingOnRequester: request info, clock paused
  WaitingOnRequester --> InProgress: requester replies, clock resumes
  InProgress --> Resolved: fix posted, clock stops
  Assigned --> Resolved: resolved directly
  Resolved --> Closed: requester confirms, or 3 business days pass
  Resolved --> Reopened: requester rejects fix
  Reopened --> InProgress: clock resumes
  Closed --> [*]

  note right of New
    decision = human_review keeps the ticket in New
    until an agent triages it (30 min owner promise)
  end note
  note right of InProgress
    is_escalated and escalation_level E1..E4
    are flags on the ticket, not states
  end note
```

### 2.2 Requester-chosen escalation (PRD 4B.6)

```mermaid
stateDiagram-v2
  [*] --> Pending: requester escalates, guardrails pass
  Pending --> Accepted: chosen member accepts, posts new ETA
  Pending --> Reassigned: chosen member names a new owner and ETA
  Pending --> Declined: returns to Team Lead with reason
  Pending --> TimedOut: response_due passes
  TimedOut --> [*]: follow-up escalation created for target's manager
  Pending --> Superseded: ticket resolved or closed first
  Accepted --> [*]
  Reassigned --> [*]
  Declined --> [*]
  Superseded --> [*]
```

### 2.3 SLA clock

```mermaid
stateDiagram-v2
  [*] --> PendingApproval: ticket needs approval
  [*] --> Running: ticket assigned
  PendingApproval --> Running: approved
  Running --> Paused: waiting on requester
  Paused --> Running: requester replies, due dates shift by paused business time
  Running --> Stopped: resolved
  Stopped --> Running: reopened
  Stopped --> [*]: closed
  state Running {
    [*] --> OnTrack
    OnTrack --> Reminder50: 50 pct used, no update
    Reminder50 --> Warning75: 75 pct used
    OnTrack --> Warning75: 75 pct used
    Warning75 --> Breached: 100 pct used, E3
    Breached --> ManagerTimeout: 2 h without manager action, E4
  }
```

### 2.4 Model lifecycle

```mermaid
stateDiagram-v2
  [*] --> Trained: dvc repro
  Trained --> Challenger: register.py
  Challenger --> Rejected: gate fails
  Challenger --> Champion: gate passes, alias set, promotion PR merged
  Champion --> Deployed: cd.yml bakes bundle into image
  Deployed --> Retired: newer champion deployed
  Deployed --> Deployed: rollback = revert promotion commit
  Rejected --> [*]
  Retired --> [*]
```

---

## 3. Sequence diagrams

### 3.1 Raise a ticket, auto-routed (FR-08 to FR-11, FR-19 to FR-22)

Screen: `/app/new` → confirmation. Tables: tickets, predictions, assignments, sla_clocks, audit_log, notifications, outbox.

```mermaid
sequenceDiagram
  autonumber
  actor R as Requester
  participant UI as React /app/new
  participant API as tickets router
  participant TC as tickets controller
  participant INF as inference
  participant ASG as assignment
  participant SLA as sla
  participant BUS as event bus
  participant DB as Postgres
  participant OB as outbox dispatcher

  R->>UI: types description, presses Submit
  UI->>API: POST /api/v1/tickets with Idempotency-Key
  API->>TC: create_ticket(cmd, user)
  TC->>DB: check idempotency key
  TC->>INF: predict(text)
  INF-->>TC: Access 0.94, High, auto_route
  TC->>DB: BEGIN
  TC->>DB: insert ticket (New to Triaged), insert prediction
  TC->>ASG: pick(ticket, now)
  ASG->>DB: read v_workload, shifts, leave, skills
  ASG-->>TC: Priya Sharma, rule trace
  TC->>DB: insert assignment, ticket to Assigned
  TC->>SLA: start_clock(ticket, now)
  SLA-->>TC: first_response_due 15:30, resolution_due 19:30
  TC->>BUS: TicketCreated, TicketAssigned, SlaClockStarted
  BUS->>DB: audit rows, in-app notifications, outbox rows (same transaction)
  TC->>DB: COMMIT
  TC-->>API: TicketCreatedOut
  API-->>UI: 201 with assignee, team, ETA
  UI-->>R: confirmation card (PRD 4B.1) within 5 s
  OB->>DB: poll outbox every 15 s
  OB-->>R: simulated email to requester and engineer
```

### 3.2 Human review and agent correction (FR-12, FR-20)

Screen: `/desk/review`. Tables: tickets, feedback, assignments, sla_clocks.

```mermaid
sequenceDiagram
  autonumber
  actor R as Requester
  actor AG as Service Desk Agent
  participant UI as React /desk/review
  participant TK as tickets
  participant FB as feedback
  participant ASG as assignment
  participant SLA as sla
  participant N as notifications

  R->>TK: POST /tickets ("outlook asks password and printer broken")
  TK-->>R: 201 decision human_review, owner named within 30 min
  TK->>N: TicketCreated(human_review) to requester and agents
  AG->>UI: opens review queue (GET /tickets?view=review_queue)
  UI->>TK: GET /tickets/T-1043/assignment-suggestion?category=Access
  TK->>ASG: pick(ticket with corrected category)
  ASG-->>UI: suggested Arjun Mehta with rule trace
  AG->>UI: correct category to Access, priority Medium, Assign
  UI->>TK: POST /tickets/T-1043/triage
  TK->>FB: record(agent_correction, Miscellaneous to Access)
  TK->>ASG: assign(Arjun)
  TK->>SLA: start_clock
  TK->>N: TicketTriaged, TicketAssigned
  N-->>R: Arjun Mehta has your ticket, ETA tomorrow 11:00
```

### 3.3 Approval step (FR-30)

```mermaid
sequenceDiagram
  autonumber
  actor R as Requester
  actor AP as Approver
  participant TK as tickets
  participant APR as approvals
  participant ASG as assignment
  participant SLA as sla

  R->>TK: POST /tickets ("need admin rights to install python")
  TK->>APR: request(ticket, approver = line manager)
  APR-->>TK: approval pending, due in 1 business day
  TK-->>R: 201 Awaiting approval from Meera Iyer, SLA starts after approval
  AP->>APR: POST /tickets/T-1044/approve
  APR->>ASG: pick(ticket)
  APR->>SLA: start_clock(now)
  APR-->>R: notification with assignee and ETA
```

### 3.4 SLA ladder tick, including a host that slept (FR-24)

```mermaid
sequenceDiagram
  autonumber
  participant CRON as GitHub cron (15 min) or APScheduler (60 s)
  participant API as POST /internal/sla/tick
  participant SLA as sla.tick(now)
  participant DB as Postgres
  participant ASG as assignment
  participant ESC as escalation
  participant N as notifications

  CRON->>API: tick (service token)
  API->>SLA: tick(now)
  SLA->>DB: acquire scheduler lease
  SLA->>DB: select running clocks where next_check_at <= now
  loop each due clock
    SLA->>SLA: used_pct = business_seconds(started, now) minus paused, over target
    alt first response missed
      SLA->>DB: insert sla_events(first_response_miss, cycle)
      SLA->>ASG: reassign to next available engineer
      SLA->>N: Team Lead told
    else crossed several thresholds while asleep
      SLA->>DB: insert sla_events pct50, pct75, breach (each once, unique key)
      SLA->>ESC: create auto escalation E3 to SD Manager
      SLA->>N: ONE combined notice for the highest step
    else 2 h after breach, manager has not acted
      SLA->>DB: insert sla_events(manager_timeout)
      SLA->>ESC: auto escalation E4 to IT Delivery Manager
    end
    SLA->>DB: update next_check_at
  end
  SLA->>DB: pending escalations past response_due to TimedOut, create follow-ups
  SLA->>DB: release lease
```

### 3.5 Requester-chosen escalation with response and timeout (FR-25 to FR-27, FR-29)

Screens: `/app/tickets/:id/escalate`, `/escalations/:id`.

```mermaid
sequenceDiagram
  autonumber
  actor R as Requester
  actor CM as Chosen member (Team Lead)
  participant UI as React escalate sheet
  participant DIR as directory
  participant ESC as escalation
  participant FB as feedback
  participant N as notifications
  participant TICK as sla tick

  R->>UI: Escalate
  UI->>DIR: GET /directory/members?for_ticket=T-1042
  DIR-->>UI: suggested first (Team Lead, SD Manager), disabled rows with reasons
  R->>UI: picks Riya Kapoor, reason wrong_team, note
  UI->>ESC: POST /tickets/T-1042/escalate
  ESC->>ESC: guardrails (owner, open, 2 per 24 h, 1 h cooldown, not self, not owner, eligible, not on leave)
  alt guardrail fails
    ESC-->>UI: 422 ESCALATION_COOLDOWN with next_allowed_at
  else passes
    ESC->>FB: wrong_team counted as model feedback
    ESC->>N: notify chosen member, assignee, Team Lead
    ESC-->>UI: 201 response due 17:30
  end
  alt chosen member responds in time
    CM->>ESC: POST /escalations/E-88/respond accept with new ETA
    ESC->>N: requester told new owner and ETA
  else no response by deadline
    TICK->>ESC: time out E-88
    ESC->>ESC: create follow-up escalation to Riya's manager
    ESC->>N: requester and new target told
  end
```

### 3.6 Engineer asks for info, clock pauses, requester replies (FR-21)

```mermaid
sequenceDiagram
  autonumber
  actor E as Engineer
  actor R as Requester
  participant TK as tickets
  participant SLA as sla
  participant N as notifications

  E->>TK: POST /tickets/T-1042/request-info ("which VPN client version?")
  TK->>SLA: pause(now)
  TK->>N: requester told, ticket shows Waiting on you
  R->>TK: POST /tickets/T-1042/messages (reply)
  TK->>SLA: resume(now), due dates shifted by paused business time
  TK->>N: engineer told, requester sees new ETA if it moved
```

### 3.7 Resolve, confirm or reopen

```mermaid
sequenceDiagram
  autonumber
  actor E as Engineer
  actor R as Requester
  participant TK as tickets
  participant SLA as sla
  participant JOB as auto-close job

  E->>TK: POST /tickets/T-1042/status Resolved with note
  TK->>SLA: stop clock, store met or breached
  TK-->>R: Is this fixed? Confirm or Reopen
  alt confirms
    R->>TK: POST /tickets/T-1042/confirm
    TK->>TK: Closed
  else reopens
    R->>TK: POST /tickets/T-1042/reopen with reason
    TK->>SLA: resume clock
  else no answer for 3 business days
    JOB->>TK: auto close
  end
```

### 3.8 Login and role routing

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant UI as React /login
  participant ID as identity
  participant DB as Postgres

  U->>UI: email and password (or Demo login, role)
  UI->>ID: POST /auth/login
  ID->>DB: find user, verify argon2 hash
  ID-->>UI: Set-Cookie session (httpOnly) and Me
  UI->>ID: GET /auth/me on every app load
  UI-->>U: redirect to role home (/app, /desk/review, /work, /team, /approvals, /insights)
```

### 3.9 CI/CD release (FR-14, FR-15)

```mermaid
sequenceDiagram
  autonumber
  actor DEV as Intern
  participant GH as GitHub
  participant CI as ci.yml
  participant CD as cd.yml
  participant ML as MLflow (DagsHub)
  participant REG as GHCR
  participant HOST as Render

  DEV->>GH: push feature branch, open PR
  GH->>CI: run
  CI->>CI: ruff, import-linter, mypy, pytest + coverage, frontend lint/test/build
  CI->>CI: data validation, smoke-train, quality gate, migration up/down, OpenAPI diff
  CI->>CI: build image, container smoke test (/ready, sample predictions)
  CI-->>GH: green, review, merge to main
  GH->>CD: run on main
  CD->>ML: download champion bundle by run_id, verify sha256
  CD->>REG: build and push image tagged git sha
  CD->>HOST: deploy hook with image tag
  CD->>HOST: poll /health then /ready, then Playwright smoke
  alt smoke fails
    CD->>HOST: redeploy previous image tag (rollback)
  else passes
    CD->>HOST: POST /internal/model-deployments
  end
```

### 3.10 Drift, retrain, promote (FR-16, FR-17)

```mermaid
sequenceDiagram
  autonumber
  participant MON as monitor.yml
  participant API as API /internal
  participant EV as Evidently
  participant GHI as GitHub Issues
  participant RT as retrain.yml
  participant DVC as DVC remote
  participant ML as MLflow
  participant GH as GitHub PR

  MON->>API: GET /internal/exports/predictions?since=7d
  MON->>DVC: pull reference features
  MON->>EV: drift report on TF-IDF features and predicted categories
  MON->>API: POST /internal/monitoring-runs
  alt breached
    MON->>GHI: open drift issue with numbers
    MON->>RT: workflow_dispatch(reason)
    RT->>API: GET /internal/exports/feedback?unexported_only=true
    RT->>DVC: dvc add feedback, dvc repro, dvc push
    RT->>ML: log runs, register challenger
    RT->>RT: quality gate vs champion
    alt gate passes
      RT->>ML: alias champion = new version
      RT->>GH: PR "Promote routing vN" with auto-merge
      RT->>API: POST /internal/exports/feedback/ack
    else gate fails
      RT->>GHI: comment gate report, champion kept
    end
  end
```

---

## 4. Data-flow diagram and trust boundaries

```mermaid
flowchart LR
  subgraph TB1["Trust boundary: user browser (untrusted)"]
    U[User input<br/>ticket text, notes]
  end
  subgraph TB2["Trust boundary: API container"]
    V[Validation<br/>schemas, limits, RBAC]
    P[Preprocess + model]
    W[Workflow modules]
  end
  subgraph TB3["Trust boundary: data stores"]
    T[(tickets: full text)]
    PL[(predictions: hash + 200 chars)]
    F[(feedback)]
    AU[(audit_log: append-only)]
  end
  subgraph TB4["Trust boundary: CI and ML platform"]
    GA[GitHub Actions<br/>service token]
    MLF[(MLflow + DVC)]
  end

  U -- HTTPS, cookie --> V
  V --> P --> W
  W --> T
  P --> PL
  W --> F
  W --> AU
  GA -- service token, exports --> PL
  GA -- service token, exports --> F
  GA --> MLF
  MLF -- signed bundle via image --> P
```

Data classification: ticket text may contain personal data in a real deployment. In this project all data is public or synthetic (PRD 3.2). Even so, the design keeps full text in one table only, logs a hash and a 200-character preview everywhere else, and exports full text only for labelled feedback rows used in training.

---

## 5. Failure modes: how the flow avoids breaking

| Failure | Where | Behaviour | User sees |
| --- | --- | --- | --- |
| Model file missing or corrupt | startup | API starts degraded, `/ready` 503, tickets go to human review | "Our service desk is reviewing this" (normal human-review copy) |
| Model raises on one input | `/tickets` | caught, ticket goes to human review with reason `model_unavailable`, error logged | same as above |
| DB down | any write | 503 `DB_UNAVAILABLE`; SPA keeps the draft in local storage and offers retry (frontend plan 6.4) | "We couldn't save that, try again" |
| Transaction fails half-way | `/tickets` | everything rolls back including audit and notification rows (single transaction) | error, no orphan ticket |
| Double submit | `/tickets`, `/escalate` | idempotency key returns the first response | one ticket |
| Host asleep when a threshold passes | scheduler | derived state + catch-up tick on wake + 15-min external cron; one combined notice | correct current state on next load |
| Two ticks at once | scheduler | lease row + `sla_events` unique key | nothing duplicated |
| Email server down | outbox | retries with backoff, dead-letter after 6 attempts, in-app notification already delivered | in-app notice arrives on time |
| No eligible engineer | assignment | Team Lead assigned and ticket flagged (PRD 4B.2 rule 5) | named owner still shown |
| Chosen escalation member on leave | escalate | 422 with delegate suggestion | "On leave until 24 Oct, suggest Arjun Mehta" |
| Respond and timeout race | escalation | conditional update, loser gets 409 or skips | one outcome |
| Bad config edit | admin | schema validation rejects; version check prevents lost updates; audit shows who changed what | console shows the validation error |
| Migration breaks | deploy | CI tests up/down on both engines; expand-and-contract; CD rollback to previous tag | no outage |
| New model worse in production | after deploy | next monitor run shows it; `git revert` promotion PR redeploys previous bundle | |
| Free-tier cold start | first request | `/health` cheap; SPA shows a "waking up the service" skeleton when the first call takes > 3 s | brief wait, documented (PRD risk table) |
| Training/serving skew | startup | preprocess fingerprint check refuses the bundle | degraded mode, alert in logs |
