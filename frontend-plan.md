# Frontend Plan: IT Ticket Auto-Routing and Priority Classifier

Companion to the PRD (v1.1, October 20, 2026) | Draft 2 (React + Streamlit split) | Covers every screen the PRD needs, the design system taken from the seven references, the component library, the API contract, and a build schedule that fits PRD Phases 3 to 7.

---

## 1. Summary and the one decision to confirm

**What we are building.** One web app with two faces:

- A **dark marketing face** (hero landing page, login and signup), styled after reference 1 and reference 7 but recoloured with our palette.
- A **warm light app face** (requester portal, agent, engineer, team lead, manager and admin consoles), styled after references 4, 5 and 6: San/cream backgrounds, soft rounded cards, Nero primary buttons and Orange as the single accent.

**Stack decision (confirmed by Hitesh, Oct 20: React + Streamlit).** The PRD names **Streamlit** for the demo UI (FR-13). Streamlit cannot reproduce the references: no custom page layouts, limited control over fonts, cards, chat bubbles, or per-role routing. So the work is split in two:

- **React app** for everything people use day to day: landing, login, requester portal, service desk, engineer, team lead, approver and manager screens.
- **Streamlit ML console** for the Platform Admin only: model info, threshold sweep, routing map, roster and SLA config, drift report and retraining runs (section 6.14). It satisfies FR-13's Streamlit requirement for the ML side and talks to MLflow and the config files directly.

React app stack:

| Layer | Choice | Why |
| --- | --- | --- |
| Framework | **React 18 + TypeScript + Vite** | Fast dev server, static build that any free host serves, no server runtime to pay for |
| Styling | **Tailwind CSS** with our tokens, plus **shadcn/ui** (Radix primitives) restyled | Accessible dialogs, selects, comboboxes and tabs out of the box; we own the styling |
| Routing | React Router v6 | Role-based route guards |
| Server state | TanStack Query | Caching, polling for SLA timers and notifications, optimistic updates |
| Forms | react-hook-form + zod | Ticket form and escalation form validation that mirrors the API's Pydantic rules |
| Charts | Recharts | KPI dashboard, threshold sweep, SLA trend |
| Icons | Lucide | Same thin line style as references 4 to 6 |
| Motion | Framer Motion (light use) | Hero entrance, card hover, toast and drawer transitions |
| Mock API | MSW (Mock Service Worker) | Frontend work starts before the FastAPI endpoints exist |
| Tests | Vitest + Testing Library, Playwright for 3 end-to-end flows | Matches the PRD's QA role |
| Hosting | Static build on the same host as the API (FastAPI serves `/`), or Vercel/Netlify free tier | Keeps the "one docker image" rule from the PRD if served by FastAPI |

Streamlit console stack: Streamlit + Plotly charts + PyYAML, themed with our tokens through `.streamlit/config.toml` (section 6.14). Section 10 shows where the cut line falls if time runs short.

---

## 2. How each reference is used

| # | Reference | What we take | What we change |
| --- | --- | --- | --- |
| 1 | Login / signup (dark, split screen) | Two-column layout: form on the left, tall rounded visual card on the right with tags and a quote card; filled dark inputs; full-width button; "or" divider; three square social buttons; orange "Sign up" link | Background becomes Nero; the right-hand gradient is rebuilt from Orange → Concrete → Nero; the quote card shows a live product stat ("68% of tickets routed automatically this week"); social buttons become **SSO (Microsoft / Google)** plus **Demo login** |
| 2 | Typography | **Chakra Petch** as both brand and UI font (Semibold, Regular, Light); deep-brown ink on cream | Adds a monospace face for ticket IDs and timers (see 3.2). Note: the Google Fonts family is spelled **Chakra Petch** |
| 3 | Colour palette | Nero, Concrete, Orange, San, exactly | Adds a cream surface and a small set of status colours derived to pass contrast (see 3.1) |
| 4 | Elements / components (mobile dashboard) | Greeting header with system status dot; icon tiles; horizontal scroll cards; list rows with chevrons; pill chips with logos; floating bottom nav with an Orange centre "+" button; bell with Orange badge | Becomes the **Requester home** and the base card/list/tile components for every role. The bottom nav is used on mobile; desktop gets a left sidebar with the same icons |
| 5 | Chat + FAQ | Chat bubbles (user right on cream, assistant left as plain text), inline attachment rows with arrow, project picker pill at the top, composer with attach and mic buttons | Becomes the **conversational ticket intake** (describe the problem, see the model's prediction live) and the **ticket conversation/activity thread**. The same row style drives the **FAQ / self-help** list |
| 6 | New automation form | Labelled stacked fields on cream, "Reveal full prompt" orange link, agent picker with avatar and model line, two-column Time / Repeats, preview card with a check, full-width Nero submit | Becomes the **Escalate ticket** form (pick a person, reason, note, preview of who gets notified) and the **Escalation tracking** card with team availability |
| 7 | Hero section (dark VC site) | Top nav with a white pill CTA; eyebrow line with dot and a monospace tag; very large light-weight headline; muted paragraph; primary + secondary pill buttons; rounded image on the right; hatched dividers; corner crop marks; logo strip in bordered cells | All colours replaced with ours (Nero background, San text, Orange accent and highlights). Image replaced by a live "ticket routing" illustration. Logo strip becomes a **stats strip** (auto-route rate, hours saved, SLA compliance, mean first response) |

---

## 3. Design system

All values below become Tailwind theme tokens and CSS custom properties in `src/styles/tokens.css`. Colours were sampled from the reference images.

### 3.1 Colour

**Brand palette (reference 3)**

| Token | Hex | Name | Main use |
| --- | --- | --- | --- |
| `--nero` | `#171717` | Nero | Dark surfaces (landing, auth), primary buttons on light, body text on light |
| `--concrete` | `#594542` | Concrete | Secondary text on light, secondary buttons, dividers on dark, avatar backgrounds |
| `--orange` | `#FD5323` | Orange | Accent fills: FAB, active nav item, badges, progress, focus ring, chart highlight |
| `--san` | `#EEE2D8` | San | App background (light face), input fills, chip fills |

**Supporting neutrals** (derived, same warm family)

| Token | Hex | Use |
| --- | --- | --- |
| `--paper` | `#F8F2ED` | Cards and raised surfaces on San (from reference 2's background) |
| `--ink` | `#360A00` | Display headings on light (from reference 2's type colour) |
| `--nero-800` | `#202020` | Inputs and cards on dark (reference 1) |
| `--nero-700` | `#2A2A2A` | Hover on dark, hatched-divider strokes |
| `--muted-light` | `#6B5A55` | Placeholder and helper text on light |
| `--muted-dark` | `#A8958E` | Muted text on Nero |
| `--line-light` | `#E2D3C7` | Borders on light |

**Accessible accent shades.** Orange `#FD5323` is a fill colour, not a text colour on light backgrounds (2.9:1 on Paper). Rules:

| Situation | Use | Contrast |
| --- | --- | --- |
| Orange text or link on light | `--orange-text` `#B83A12` | 5.2:1 on Paper, 4.5:1 on San |
| Text or icon on an Orange fill | Nero `#171717` (preferred) | 5.5:1 |
| White on Orange fill | Only bold 19px+ or icons (like the "+" FAB) | 3.3:1 (large text only) |
| Orange text on Nero | Allowed | 5.5:1 |
| Concrete text on San / Paper | Allowed | 7.0:1 / 8.0:1 |

**Semantic colours** (used sparingly; always paired with an icon or label, never colour alone)

| Meaning | Text / icon on light | Tint background | Used for |
| --- | --- | --- | --- |
| Critical / danger / breached | `#B42318` | `#F9E1DC` | Critical priority, SLA breached, decline |
| High / attention | `#B83A12` (orange-text) | `#FDE3D8` | High priority, escalated |
| Warning / at risk | `#8A5A00` | `#F6E7C8` | SLA 75% warning, awaiting approval |
| Success / on track | `#2E7D32` | `#DDEBDD` | Resolved, on track, auto-routed, available |
| AI / model | `#7D5A9B` | `#E9E0F0` | Model prediction chips, confidence (purple from reference 4's agent tile) |
| Neutral | `#594542` | `#EEE2D8` | Low priority, closed, off shift |

**Priority mapping:** Critical = danger, High = orange, Medium = warning, Low = neutral.
**Decision mapping:** `auto_route` = success chip "Auto-routed"; `human_review` = AI chip "In review".
**SLA bar:** green under 50%, amber 50 to 75%, orange 75 to 100%, red when breached.

### 3.2 Typography (reference 2)

| Role | Font | Weight | Size / line height (desktop) | Mobile |
| --- | --- | --- | --- | --- |
| Hero display | Chakra Petch | Light 300 | 72 / 76, tracking -2% | 44 / 48 |
| H1 page title | Chakra Petch | Semibold 600 | 36 / 44 | 28 / 34 |
| H2 section | Chakra Petch | Semibold 600 | 24 / 32 | 20 / 28 |
| H3 card title | Chakra Petch | Semibold 600 | 18 / 26 | 17 / 24 |
| Body | Chakra Petch | Regular 400 | 16 / 24 | 15 / 22 |
| Body small / helper | Chakra Petch | Regular 400 | 14 / 20 | 14 / 20 |
| Label / overline | Chakra Petch | Regular 400 | 13 / 18 (overline: uppercase, +6% tracking) | same |
| Numbers in KPIs | Chakra Petch | Semibold 600, tabular numerals | 32 / 36 | 28 / 32 |
| Ticket IDs, timers, eyebrow tags | JetBrains Mono | Regular 400 | 13 / 18, uppercase for tags | same |

Load via Google Fonts (`Chakra Petch: 300,400,600` and `JetBrains Mono: 400`) with `font-display: swap`. Light 300 is only for display sizes; it is too thin for body text.

### 3.3 Shape, spacing, depth

| Token | Value | Reference |
| --- | --- | --- |
| Spacing scale | 4, 8, 12, 16, 20, 24, 32, 40, 56, 80 px | |
| Radius: input / small chip | 10 px | Reference 1 inputs |
| Radius: card / tile / list row | 16 px | Reference 4 tiles, reference 5 rows |
| Radius: large panel / auth visual / hero image | 24 px | References 1 and 7 |
| Radius: buttons, chips, nav | full pill | References 4 and 7 |
| Shadow on light | `0 1px 2px rgba(54,10,0,.06), 0 4px 16px rgba(54,10,0,.06)` | Soft lift seen in reference 4 |
| Tile inner highlight | 1 px inset `rgba(255,255,255,.7)` on Paper | Reference 4's frosted tiles |
| Dark surfaces | no shadow; 1 px `--nero-700` border | Reference 7 |
| Page gutter | 16 px mobile, 24 px tablet, 32 px desktop; max content 1280 px | |
| Breakpoints | 640, 768, 1024, 1280 | |

### 3.4 Motion

150 ms ease-out for hover and press; 220 ms for drawers and dialogs; hero headline fades and rises 12 px on load; respect `prefers-reduced-motion` (no movement, opacity only).

### 3.5 Iconography and imagery

Lucide icons at 20 px, 1.75 px stroke. Team avatars are initials on Concrete with San text. Resolver team icons: Access = `key-round`, Admin rights = `shield-check`, Hardware = `laptop`, Storage = `hard-drive`, HR = `users`, Purchase = `shopping-cart`, Internal Project = `folder-git-2`, Service Desk = `headset`.

---

## 4. Component library

Built in `src/components/ui` (primitives) and `src/components/domain` (ticket-specific). Each one gets a Storybook-style demo page at `/dev/components` (a simple route, no Storybook dependency).

### 4.1 Primitives

| Component | Variants and notes | Reference |
| --- | --- | --- |
| Button | `primary` (Nero fill, San text, pill), `accent` (Orange fill, Nero text), `secondary` (Paper fill, Nero text, 1 px line), `ghost`, `link` (orange-text), `light-pill` (white on dark, for hero/auth); sizes sm 36, md 44, lg 52; loading state | 1, 6, 7 |
| IconButton | Square 44 px, radius 14, Paper fill; `dark` variant (Nero, like the bell); notification dot | 4, 5 |
| FAB | 56 px Orange circle with white "+" icon, centred in the mobile nav | 4 |
| Input / Textarea | Filled (San on light, `--nero-800` on dark), no border until focus, 2 px Orange focus ring, label above, helper and error text below | 1, 6 |
| Select / Combobox | Pill-shaped trigger with chevron; combobox with search for the directory | 6 |
| Chip / Badge | Tinted semantic chip with icon; `tag` variant (small rectangle, like "Product Company" on reference 1) | 1, 4 |
| Card | Paper fill, radius 16, soft shadow; `interactive` variant lifts 2 px on hover | 4 |
| Tile | Square card with circular coloured icon and uppercase label | 4 (agents row) |
| ListRow | Full-width row, title, optional meta, trailing chevron or arrow-up-right | 4, 5 |
| Tabs / SegmentedControl | Pill segments on San | |
| Dialog / Drawer / Sheet | Radix-based, Paper surface, radius 24; bottom sheet on mobile | |
| Toast | Nero surface with San text, Orange left bar for important events | |
| Avatar / AvatarStack | Initials on Concrete, presence dot (green on shift, grey off shift, amber on leave) | 6 |
| ProgressBar / SLA bar | 6 px track on San, coloured fill per 3.1 | |
| Divider with label | Thin line with centred "or" | 1 |
| HatchedDivider | Diagonal 45° stripes in `--nero-700`, 56 px tall | 7 |
| CropFrame | Four corner marks around a hero block | 7 |
| EmptyState | Line icon, one sentence, one action | |
| Skeleton | Shimmer on San | |

### 4.2 Domain components

| Component | What it shows |
| --- | --- |
| `TicketCard` | ID (mono), title, category icon, priority chip, status chip, assignee avatar, SLA bar with time remaining |
| `PredictionPanel` | Category with confidence bar, priority with confidence, decision chip, routed team, model version (mono), "Correct this" button (FR-12) |
| `AssignmentSummary` | The PRD 4B.1 confirmation: assignee, team, first response by, expected resolution by, Escalate link |
| `SlaTimer` | Live countdown, colour per SLA state, "paused, waiting on you" state |
| `StatusStepper` | New → Triaged → Assigned → In progress → Resolved → Closed, with side-state badges (Awaiting approval, Waiting on requester, Escalated, Reopened) |
| `ActivityTimeline` | Audit log entries with icon, actor, action, time; system and escalation events styled distinctly (FR-23, FR-28) |
| `EscalationLadder` | E1 to E4 vertical track, current level highlighted in Orange, timestamps for each step reached (4B.5) |
| `EscalationCard` | Reason, chosen member, response deadline countdown, outcome (Accept / Reassign / Decline / Timed out) |
| `MemberPicker` | Searchable directory combobox: avatar, name, role, team, availability dot, suggested members (Team Lead, SD Manager) pinned first, disabled rows with reasons (self, current owner, on leave → "suggest delegate") |
| `TeamAvailabilityGrid` | For each team: members with shift status, open workload versus daily capacity bar, skill tags |
| `KpiTile` | Label, big number, delta versus last period, sparkline |
| `ChatBubble` / `ChatComposer` | Reference 5 styling; composer with attach, text, send (mic button omitted in v1, see 12) |
| `FaqItem` | Accordion row with chevron; "Still stuck? Raise a ticket" footer |
| `NotificationItem` | Event icon, sentence, ticket link, time, unread dot |

---

## 5. Roles, navigation and routes

Roles come from PRD 4A.1. One login; the role on the account decides the home screen and the nav. A demo account per role is listed on the login page.

| Role | Home route | Main nav items |
| --- | --- | --- |
| Requester | `/app` | Home, Raise ticket (FAB), My tickets, Help/FAQ, Notifications |
| Service Desk Agent (L1) | `/desk/review` | Human Review queue, All tickets, Directory, Notifications |
| Resolver Engineer (L2) | `/work` | My queue, Ticket detail, Notifications |
| Team Lead | `/team` | Team board, Workload and availability, Escalations, SLA warnings |
| Approver | `/approvals` | Pending approvals, History |
| SD Manager / IT Delivery Manager | `/insights` | KPI dashboard, SLA and escalations, Breaches, All tickets |
| Platform Admin (MLOps) | Streamlit console at `/console` | Model, Threshold, Routing map, Roster, SLA policy, Monitoring |

**Full route map**

```
/                         Landing page (hero)                       public
/login  /signup           Auth                                      public
/help                     FAQ and self-help                          public + requester

/app                      Requester home                            requester
/app/new                  Raise ticket (chat intake or form)        requester
/app/tickets              My tickets                                requester
/app/tickets/:id          Ticket status page                        requester (own tickets)
/app/tickets/:id/escalate Escalate (sheet over the status page)     requester

/desk/review              Human Review queue                        agent
/desk/tickets             All tickets (search, filter)              agent, lead, manager
/tickets/:id              Staff ticket view                         staff roles

/work                     Engineer queue                            engineer
/team                     Team board                                lead
/team/availability        Team availability and workload            lead, manager
/escalations              Escalation tracking                       lead, manager, chosen members
/escalations/:id          Respond to escalation                     chosen member

/approvals                Approvals                                 approver
/insights                 KPI and SLA dashboard                     manager
/console  (Streamlit)     Model, threshold, routing, roster, SLA, monitoring   admin, linked from the React sidebar
/notifications            Notification centre                       all signed-in
```

**Shell.** Desktop: 248 px left sidebar on Paper (logo, role nav, user card at the bottom), top bar with page title, global search, bell and avatar. Mobile: top bar plus the floating bottom nav from reference 4 (Home, My tickets, Orange "+" FAB, Help, Profile). Staff roles on mobile get a simplified list view; dense tables collapse to `TicketCard` stacks.

---

## 6. Screen specifications

Each screen lists layout, content, states and the PRD requirement it covers.

### 6.1 Landing page `/` (references 7 + 3)

- **Nav bar:** logo mark (two Orange rounded bars echoing reference 7's mark) + "RouteDesk" placeholder name; links About, How it works, Teams, FAQ; light-pill CTA "Raise a ticket"; secondary text link "Sign in".
- **Hatched divider** under the nav, then a **CropFrame** around the hero block, two columns split by a 1 px vertical line.
- **Left column:** eyebrow `● Live` + mono tag `IT SERVICE DESK / AUTO-ROUTING`; headline in Light 300 "Every ticket, in the right hands, in seconds"; muted paragraph (San at 70%) on what it does; buttons: light-pill "Raise a ticket", dark-pill "See how routing works".
- **Right column:** rounded 24 px panel with an animated illustration: a ticket card slides in, a prediction chip appears ("Access · 0.94"), an Orange line routes it to a team avatar, then the ETA chip appears. Built in SVG + Framer Motion; a static frame for reduced motion.
- **Hatched divider**, then a **stats strip** in bordered cells (reference 7's logo strip): Auto-route rate, Routing accuracy, Hours saved this month, SLA compliance, Mean first response. Values from `GET /kpis/public` (fallback to demo values labelled "demo data").
- Below the fold: "How it works" (three steps: Describe, We route, Track and escalate), resolver teams grid (8 tiles with icons from 3.5), FAQ preview (5 items → `/help`), footer.
- Colours: background Nero, text San, accent Orange, borders `--nero-700`.

### 6.2 Login and signup `/login`, `/signup` (reference 1)

- Nero page. Left column (max 480 px): logo, "Welcome back!" (H1), one-line subtitle, Email, Password (with show/hide), "Forgot password?" link, Nero-800 full-width "Sign in" button that turns Orange on hover/focus, "or" divider, SSO buttons (Microsoft, Google) and a **Demo login** button that opens a role picker (Requester, Agent, Engineer, Team Lead, Approver, Manager, Admin).
- Footer line: "New here? **Sign up**" in Orange (fixes reference 1's copy, which says "Already have an account?" on the sign-in page).
- Right column: 24 px rounded visual with an Orange → Concrete → Nero gradient and faint rotated rounded squares (reference 1's shapes); tags "Auto-routed" and "SLA on track"; glass quote card (Nero at 60% with blur) showing a live stat or a testimonial-style line from a team lead persona.
- Signup: name, work email, department, password, confirm. New accounts are Requesters; staff roles come from the roster (PRD 4A.1).
- States: field errors under inputs, a banner for wrong credentials, a loading state on the button, lockout message after 5 attempts.
- Below 1024 px the visual card is hidden; the form stays centred.

### 6.3 Requester home `/app` (reference 4)

- Header: status dot + "All systems on" (or "Known issue: VPN degraded" in amber, from a service-status flag), greeting "Morning, {first name}!", bell icon button (Nero) with Orange badge.
- **Quick help tiles** (reference 4's Agents row): 3 to 4 tiles for the most common requests (Password reset, VPN access, New hardware, Software install). Tapping one opens `/app/new` with the category pre-hinted in the text.
- **Open tickets** (reference 4's Automations row): horizontal scroll of `TicketCard`s showing assignee, ETA, SLA bar.
- **Recent conversations / updates** (reference 4's Active chats): `ListRow`s like "T-1042 · Priya posted an update".
- **Help articles** (reference 4's Providers row): chip pills linking to FAQ categories.
- Mobile bottom nav with the Orange "+" FAB = Raise ticket.
- Empty state: "No open tickets. Need help? Raise a ticket or browse FAQs."

### 6.4 Raise ticket `/app/new` (reference 5)

Two modes behind a segmented control: **Chat** (default) and **Form**.

- **Chat mode:** the assistant greets and asks what is wrong. The requester types freely. On send, the frontend calls `POST /predict` (debounced, not on every keystroke) and shows an inline "I think this is **Access** (94%) for the **Access and Identity Team**, priority **High**" card with Confirm and "Not quite" actions. "Not quite" lets them pick a category, which is sent as feedback. Before submitting, the assistant suggests up to 3 FAQ articles that match the category (self-help deflection, links open in a drawer). Attachments appear as reference 5's file rows.
- **Form mode:** Subject, Description (5,000-character limit with counter, matching PRD NFR), optional attachment, optional "This is blocking my whole team" toggle (feeds the rule-based priority override, PRD 9.2).
- **Submit** → `POST /tickets`. Show the **confirmation screen** within the 5-second target (PRD 3.3): `AssignmentSummary` card exactly as PRD 4B.1, with Category, Priority, Assigned to, First response by, Expected resolution by, and an "Escalate" link. If the decision is `human_review`, show "Our service desk is reviewing this. An owner will be named within 30 minutes" instead of an assignee.
- For Administrative rights and Purchase, show an "Awaiting approval from {approver}" step and explain that the SLA clock starts after approval (FR-30).
- Errors: empty text, over 5,000 characters, API down (keep the draft in local storage and offer retry).

### 6.5 My tickets `/app/tickets`

Tabs: Open, Waiting on me, Resolved. `TicketCard` list with search. Badge on "Waiting on me" when an engineer asked a question (the SLA clock is paused).

### 6.6 Ticket status page `/app/tickets/:id` (FR-22, FR-23)

- Header: mono ID, title, priority chip, status chip, escalation level chip (E1 to E4).
- Left (2/3 width): `StatusStepper`; conversation thread in reference 5's bubble style (requester ↔ engineer messages, system events as small centred lines); composer at the bottom.
- Right (1/3): `AssignmentSummary` (owner, team, first response by, ETA with countdown `SlaTimer`), "ETA changed" history with reasons, `EscalationLadder`, the model's prediction (read-only for requesters), and an **Escalate** button (secondary, Orange text).
- Resolved state: banner "Is this fixed?" with **Confirm** and **Reopen** (lifecycle 4B.4).
- Mobile: single column, the summary card sticks to the top in a collapsed form.

### 6.7 Escalate flow `/app/tickets/:id/escalate` (reference 6, FR-25, FR-26)

Opens as a right-side sheet (desktop) or full-screen sheet (mobile), laid out like reference 6:

1. **Ticket summary** (reference 6's "Task goal" box) with an Orange "View full ticket" link.
2. **Escalate to** (reference 6's "Designated Agent" picker): `MemberPicker`. Suggestions first: the assignee's Team Lead and the Service Desk Manager. Each row shows avatar, name, role, team, availability. Disabled rows explain why: "You", "Current owner", "On leave until 24 Oct, suggest delegate: Arjun Mehta".
3. **Reason** (required): segmented chips No response, Wrong team, Business-critical, Deadline at risk, Other.
4. **Note** (required, 10 to 500 characters).
5. **Preview card** (reference 6's bottom card): "Riya Kapoor (Team Lead, Access) will be asked to respond by 5:30 PM. Priya Sharma and the Team Lead will also be notified." Response window: 2 business hours, or 30 minutes for Critical.
6. **Submit**: full-width Nero "Escalate ticket".

Guardrail UI: if 2 escalations were used in 24 hours or the 1-hour cooldown is active, the button is disabled with "You can escalate again at 4:10 PM". Server errors from `POST /tickets/{id}/escalate` map to inline messages. "Wrong team" shows a note that this also helps improve routing (FR-29).

### 6.8 Escalation tracking `/escalations` and team availability `/team/availability` (reference 6)

- **Escalation board** (lead, manager): columns Awaiting response, Accepted, Reassigned, Declined, Timed out → moved to manager. Each `EscalationCard` shows ticket, requester, reason, chosen member, live response-deadline countdown, and audit link. Filters: team, reason, level (requester-chosen versus automatic ladder E2 to E4).
- **Respond to escalation** `/escalations/:id` (chosen member): ticket summary, requester's reason and note, three large actions **Accept** (asks for a new ETA), **Reassign** (`MemberPicker` + new ETA), **Decline** (reason required). Calls `POST /escalations/{id}/respond` (FR-27).
- **Team availability**: `TeamAvailabilityGrid`, one card per resolver team: members with on-shift / off-shift / on-leave dots, open workload versus daily capacity bars, skill tags, and an "escalation-eligible" marker. A "Who can take this now?" filter by skill tag. Data from `GET /roster/workload` and `GET /directory/members`.

### 6.9 Human Review queue `/desk/review` (agent, PRD user stories)

- Table (desktop) / cards (mobile): ID, received time, snippet, predicted category + confidence bar, predicted priority, reason it is here (low confidence, multi-issue, Miscellaneous), SLA timer for the 30-minute owner promise.
- Row click opens a split view: full text on the left, `PredictionPanel` on the right with one-click **Correct category** and **Correct priority** (FR-12 feedback), **Assign** (auto-suggests the engineer the assignment engine would pick, with an option to choose another), and **Resolve directly** for simple requests.
- Keyboard shortcuts: J/K to move, A to accept prediction, C to correct.

### 6.10 Engineer queue `/work` and staff ticket view `/tickets/:id`

- Queue sorted by SLA risk, with chips for priority and side states. Counters: open, due today, at risk, breached.
- Staff ticket view adds to the requester view: **Update status** (with note), **Change ETA** (reason required, FR-21/22), **Request info** (moves to Waiting on requester and pauses the clock), **Hand back** (reason), and the full audit log tab (FR-28).

### 6.11 Team board `/team` (Team Lead)

Kanban by status for the lead's team, SLA warning lane at the top (75%+ used), reassign by dragging or via a menu (`POST /tickets/{id}/reassign`), workload strip per engineer.

### 6.12 Approvals `/approvals` (Approver, FR-30)

List of Administrative rights and Purchase tickets awaiting sign-off with requester, item, justification, and Approve / Reject (reason required). Target: 1 business day, shown as a timer.

### 6.13 Insights dashboard `/insights` (manager, FR-31, PRD 12 KPIs)

- Top row of `KpiTile`s: auto-route rate, accuracy on reviewed tickets, override rate, average confidence, SLA compliance, escalation rate, mean time to first response, cumulative hours saved.
- Charts: tickets per category (bar), auto-route rate over time (line), SLA compliance by team (bar), escalations by reason (bar), workload per engineer (horizontal bar), hours saved cumulative (area).
- **Hours-saved calculator** card that shows the PRD 12 formula with the current N, a, p, t, c, r, with inputs editable by the manager (labelled as assumptions).
- Date range filter and team filter. Charts follow the palette: Orange for the highlighted series, Concrete and muted tints for the rest.

### 6.14 ML console in Streamlit `/console` (Platform Admin)

A multipage Streamlit app (`ui/streamlit_app.py` + `ui/pages/`, matching the PRD's repo layout). It reads MLflow, the prediction and feedback logs, and the YAML configs directly, so it needs almost no new API endpoints. The React sidebar shows an "ML console" link for the admin role only; the console is protected by the same demo login (shared secret or a token check against `GET /auth/me`).

**Theming so it matches the React app** (`.streamlit/config.toml`): `base="light"`, `primaryColor="#FD5323"`, `backgroundColor="#EEE2D8"`, `secondaryBackgroundColor="#F8F2ED"`, `textColor="#171717"`, and Chakra Petch loaded through a small CSS injection with `st.markdown(..., unsafe_allow_html=True)`. Charts use Plotly with the same palette (Orange highlight, Concrete and tints for the rest).

| Page | Content | Source |
| --- | --- | --- |
| Model | Champion version, metrics, registered date, MLflow run comparison table | MLflow client, `GET /model-info` |
| Threshold | Current threshold, slider over the validation sweep chart (a, p, net hours saved, with the p ≥ 90% line), "Apply" writes params.yaml | Sweep artifact from MLflow, params.yaml |
| Routing map | Category → team table, editable with `st.data_editor` | routing_map.yaml |
| Roster | Members table with skills, shifts, capacity, leave, eligibility | roster.yaml |
| SLA policy | Read-only view of sla.yaml and escalation_rules.yaml in tables | YAML files |
| Monitoring | Latest Evidently report embedded with `st.components.v1.html`, low-confidence rate, override rate, drift flag, last retrain run and champion vs challenger | Monitoring reports folder, prediction and feedback logs, MLflow |
| Playground | Paste a ticket, see raw `/predict` output with confidences per class (handy for the demo video and debugging) | `POST /predict` |

Config edits (threshold, routing map, roster) are **Could**; read-only views are enough for the demo. Edits write the YAML and the API picks them up on its next config reload.

### 6.15 Help and FAQ `/help` (reference 5)

Search box, category chips (matching the 8 resolver categories), accordion `FaqItem`s in reference 5's row style, each answer ending with "Still stuck? Raise a ticket" that opens `/app/new` with the category hinted. FAQ content lives in a JSON file in the frontend repo (`src/content/faq.json`) so it needs no backend work.

### 6.16 Notifications `/notifications` and the bell

Bell dropdown shows the latest 10; the full page groups by day. Every event in PRD 4B.1 has an icon and sentence template. Polled every 30 seconds via TanStack Query (no WebSocket needed for the demo; SSE is an optional upgrade).

---

## 7. API contract the frontend needs

**Existing in the PRD**

| Endpoint | Used by |
| --- | --- |
| `POST /predict` | Chat intake live prediction |
| `POST /feedback` | Correct category / priority |
| `GET /health` | Status dot on home, admin |
| `GET /model-info` | Admin, prediction panel footer |
| `POST /tickets` | Raise ticket |
| `GET /tickets/{id}` | Status page, staff view |
| `POST /tickets/{id}/status` | Engineer updates, ETA changes |
| `POST /tickets/{id}/reassign` | Agent, Team Lead |
| `POST /tickets/{id}/escalate` | Escalate flow |
| `POST /escalations/{id}/respond` | Chosen member |
| `GET /directory/members` | Member picker, availability |
| `GET /roster/workload` | Availability, team board, insights |

**Missing endpoints the frontend needs** (to hand to the backend owner; all small)

| Endpoint | Purpose | Priority |
| --- | --- | --- |
| `POST /auth/login`, `POST /auth/signup`, `GET /auth/me` | Session and role (JWT or cookie). Demo users seeded from roster.yaml plus requesters | Must |
| `GET /tickets?role=&status=&team=&assignee=&q=` | Lists for every queue | Must |
| `GET /tickets/{id}/messages`, `POST /tickets/{id}/messages` | Conversation thread | Must (Should if time is short: show the activity timeline only) |
| `GET /notifications`, `POST /notifications/{id}/read` | Bell and notification centre | Must |
| `GET /escalations?status=&team=` | Escalation board | Must |
| `POST /tickets/{id}/confirm`, `POST /tickets/{id}/reopen` | Requester closes or reopens | Must |
| `POST /tickets/{id}/approve`, `POST /tickets/{id}/reject` | Approvals | Should |
| `GET /kpis?from=&to=&team=` | Insights dashboard | Should |
| `GET /kpis/public` | Landing stats strip | Could |

Also needed from the backend: CORS for the frontend origin, consistent error shape `{ code, message, field? }`, and timestamps in ISO 8601 with timezone so ETAs render in the user's local time.

**Typing.** Generate TypeScript types from FastAPI's OpenAPI schema with `openapi-typescript` so the frontend and Pydantic models never drift apart.

---

## 8. Frontend architecture

```
frontend/
  index.html
  vite.config.ts  tailwind.config.ts  tsconfig.json
  src/
    main.tsx  App.tsx  router.tsx
    styles/        tokens.css  globals.css
    lib/           api.ts (fetch wrapper)  auth.ts  time.ts (business-hours formatting)  cn.ts
    api/           generated/ (openapi types)  tickets.ts  escalations.ts  directory.ts  kpis.ts ...
    mocks/         handlers.ts  fixtures/ (roster, tickets, kpis)   ← MSW
    components/
      ui/          Button, Input, Card, Tile, ListRow, Chip, Dialog, Sheet, Toast, Avatar ...
      domain/      TicketCard, PredictionPanel, AssignmentSummary, SlaTimer, EscalationLadder,
                   MemberPicker, TeamAvailabilityGrid, KpiTile, ChatBubble, FaqItem ...
      layout/      PublicLayout (dark), AppShell (light, sidebar + bottom nav), RoleGuard
    features/
      landing/  auth/  requester/  intake/  tickets/  escalation/  desk/  engineer/
      team/  approvals/  insights/  admin/  help/  notifications/
    content/       faq.json  copy.ts
  tests/           unit and component tests
  e2e/             Playwright: raise-ticket, escalate, review-and-correct
```

**Key practices**

- **Mock first.** MSW serves fixtures shaped exactly like the API so every screen can be built and demoed before Phase 4's backend is ready. Switch with `VITE_USE_MOCKS=true`.
- **Time.** All SLA countdowns are computed from server timestamps (`first_response_due`, `resolution_due`, `paused_at`), never from client timers alone, matching the PRD's "derive SLA state from timestamps" rule. `SlaTimer` re-renders every 30 seconds.
- **Polling.** Ticket detail and queues refetch every 30 seconds and on window focus; after any mutation, invalidate the related queries.
- **Auth.** Token in an httpOnly cookie (preferred) or memory; `RoleGuard` protects routes; 401 sends the user to `/login` with a return URL.
- **Errors.** One error boundary per route; API errors become toasts or inline field errors.
- **Accessibility.** WCAG 2.1 AA: contrast rules in 3.1, visible focus ring (2 px Orange + 2 px offset), every icon button has an `aria-label`, status chips include text, live regions announce new notifications and countdown state changes (not every tick), all flows keyboard-only tested.
- **Performance.** Route-level code splitting; Recharts only loaded on `/insights` and `/admin`; fonts subset to Latin. Target: Lighthouse 90+ on the landing page and LCP under 2.5 s on the free-tier host.
- **Lint and format.** ESLint + Prettier, run in the same GitHub Actions CI as the Python checks (adds a `frontend` job to ci.yml: install, lint, typecheck, test, build).
- **Deployment.** `npm run build` outputs `dist/`; the Dockerfile copies it into the API image and FastAPI serves it with `StaticFiles` (one image, one URL, as the PRD wants). Optional: deploy `dist/` to Netlify/Vercel and point it at the API URL.
- **Streamlit console deployment.** Runs as a second service in docker-compose (`streamlit run ui/streamlit_app.py --server.baseUrlPath=console`). On a single free-tier host, run both processes in one container behind a tiny reverse proxy (Caddy), or deploy the console separately to Streamlit Community Cloud or Hugging Face Spaces; the React link just points at its URL.

---

## 9. Responsive behaviour

| Screen | Mobile (< 768) | Desktop (≥ 1024) |
| --- | --- | --- |
| Landing | Single column, illustration below the text, stats strip as a 2-column grid | Two columns with crop frame |
| Auth | Form only | Form + visual card |
| Requester app | Reference 4 layout with bottom nav and FAB | Sidebar shell, home as a 3-column card grid |
| Ticket status | Single column, collapsible summary | Thread + side panel |
| Escalate | Full-screen sheet | 480 px right sheet |
| Queues and boards | Card lists | Tables and kanban |
| Insights | Tiles 2 per row, charts stacked | 4 tiles per row, 2-column charts |

The requester experience is designed mobile first (references 4 to 6 are phone screens); staff consoles are designed desktop first.

---

## 10. Build schedule mapped to the PRD phases

The PRD has one intern for 22 days, with UI work inside Phases 3 and 4. Frontend work is spread so it never blocks the Must items of the ML pipeline.

| PRD phase (days) | Frontend work | Exit check |
| --- | --- | --- |
| 0 (1–2) | Scaffold Vite + TS + Tailwind; tokens.css; fonts; ESLint; add `frontend` CI job | `npm run build` passes in CI |
| 1–2 (3–9) | 1 to 2 hours a day only: build primitives (4.1) and the `/dev/components` page; MSW fixtures from the PRD's sample data | All primitives render in both faces |
| 3 (10–12) | Landing page, auth with demo login, AppShell, Raise ticket (form mode) with live `/predict`, prediction panel, Human Review queue with feedback; Streamlit console skeleton with theme and Playground page | Paste a ticket, see the prediction and decision, correct it |
| 4 (13–16) | Confirmation screen, ticket status page, escalate flow, respond to escalation, engineer queue, team availability, notifications | PRD Phase 4 exit criteria visible in the UI: named assignee and ETA, ladder climbs, custom escalation accepted |
| 5 (17–18) | Serve `dist/` from FastAPI in the Docker image; deploy; Playwright smoke test against the live URL | Live URL shows the landing page and login |
| 6 (19–21) | Insights dashboard (React); Streamlit console: model, threshold sweep and monitoring pages; chat intake mode | KPIs and drift report visible |
| 7 (22) | FAQ content, polish, screenshots for the README, record the UI parts of the demo video | Demo script runs start to finish |

### Cut line (if time runs short)

Cut in this order, matching the PRD's MoSCoW rule:

1. **Could:** landing page animation (use a static image), chat intake mode (keep form mode), config edits in the Streamlit console, public KPI endpoint, mic button, dark-mode toggle for the app face.
2. **Should:** approvals screen (show the state as a chip only), team kanban (keep a table), insights charts beyond the 8 KPI tiles.
3. **Never cut:** login with roles, raise ticket with prediction, confirmation with assignee and ETA, ticket status page with timeline and Escalate, escalate flow with guardrails, respond to escalation, Human Review queue with feedback, KPI tiles.

---

## 11. Testing plan

| Level | What | Tool |
| --- | --- | --- |
| Unit | Business-hours and countdown formatting, SLA colour thresholds, guardrail messages, zod schemas | Vitest |
| Component | MemberPicker disabled rules, SlaTimer states, PredictionPanel decision display, Escalate form validation | Testing Library |
| Contract | Generated types compile against the live OpenAPI schema in CI | openapi-typescript + tsc |
| End to end | (1) Requester raises a ticket and sees assignee and ETA within 5 s; (2) requester escalates, chosen member accepts, requester sees the new owner; (3) agent corrects a low-confidence ticket | Playwright (with MSW locally, live API in CD smoke test) |
| Accessibility | axe checks on every route; keyboard-only run of the three E2E flows | @axe-core/playwright |
| Visual | Screenshots of key screens at 375 px and 1280 px for review | Playwright |

---

## 12. Open questions

1. **Stack:** decided: React for user-facing screens, Streamlit for the ML console. Confirm with the mentor that this split meets FR-13.
2. **Product name and logo:** "RouteDesk" is a placeholder.
3. **Auth:** demo login with seeded roles is assumed; does the firm want real SSO later?
4. **Chat intake:** is a chat-style intake wanted in v1, or is the form enough for the demo? (Chat is on the Could list.)
5. **Voice input** (reference 5's mic button): left out of v1; confirm.
6. **App theme:** the plan uses dark for public pages and the light San theme for the app, as the references do. Is a dark mode for the app wanted?
7. **FAQ content:** who writes the articles? The plan seeds ~20 from the PRD's example tickets.
8. **Notification channel** (PRD open question): the UI covers in-app; email/Slack are backend-only.

---

## Appendix A: Tailwind token sketch

```ts
// tailwind.config.ts (excerpt)
theme: {
  extend: {
    colors: {
      nero: { DEFAULT: '#171717', 800: '#202020', 700: '#2A2A2A' },
      concrete: '#594542',
      orange: { DEFAULT: '#FD5323', text: '#B83A12' },
      san: '#EEE2D8',
      paper: '#F8F2ED',
      ink: '#360A00',
      muted: { light: '#6B5A55', dark: '#A8958E' },
      line: { light: '#E2D3C7' },
      status: {
        danger: '#B42318', 'danger-bg': '#F9E1DC',
        warning: '#8A5A00', 'warning-bg': '#F6E7C8',
        success: '#2E7D32', 'success-bg': '#DDEBDD',
        ai: '#7D5A9B', 'ai-bg': '#E9E0F0',
      },
    },
    fontFamily: {
      sans: ['"Chakra Petch"', 'system-ui', 'sans-serif'],
      mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
    },
    borderRadius: { input: '10px', card: '16px', panel: '24px' },
    boxShadow: {
      card: '0 1px 2px rgba(54,10,0,.06), 0 4px 16px rgba(54,10,0,.06)',
    },
  },
}
```

## Appendix B: Sample copy

- Confirmation: "Ticket T-1042 received. Priya Sharma from the Access and Identity Team has it. First response by 3:30 PM, fix expected by 7:30 PM today."
- Human review: "Our service desk is taking a look. You'll know who owns this within 30 minutes."
- Breach: "We missed the time we promised. Rahul Verma (Service Desk Manager) now owns this and commits to 10:00 AM tomorrow."
- Cooldown: "You can escalate this ticket again at 4:10 PM."
- Wrong-team note: "Choosing 'Wrong team' also helps our routing learn."
