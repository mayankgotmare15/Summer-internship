# RouteDesk Mobile App: Phase-Wise Development & Execution Tracker

Companion to [android-app-plan.md](../android-app-plan.md), [backend-changes-for-mobile.md](../backend-changes-for-mobile.md), and [07-mobile-app-implementation-plan.md](07-mobile-app-implementation-plan.md).

This living document provides the **granular task-by-task development breakdown**, tracking matrix, component deliverables, and acceptance criteria for every phase of building the RouteDesk native Android application.

---

## 1. Master Development Dashboard

| Phase | Focus Area | Target Window | Status | Completion | Lead / Assignee | Blockers / Dependencies |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **Phase 0** | Scaffolding, Tooling & Contracts | Week 1 (Days 1–3) | `Complete` | 100% | Mobile Lead | None (Verified with MockWebServer) |
| **Phase 1** | Design System Primitives & Auth | Week 1 (Days 3–5) | `Complete` | 100% | UI / Core Eng | None (Auth & Tokens Verified) |
| **Phase 2** | Requester Flow, Intake ML & Outbox | Week 2 (Days 6–10) | `Complete` | 100% | Feature Eng | None (Room & WorkManager Active) |
| **Phase 3** | Push Notifications, Escalations & Inbox | Week 3 (Days 11–15) | `In Progress` | 0% | Core / Feature | B2 (Devices), B3 (FCM Outbox) |
| **Phase 4** | Staff Workspaces (5 Roles) & Actions | Week 4 (Days 16–20) | `Planned` | 0% | Feature Eng | B6 (Attachments) |
| **Phase 5** | Hardening, Performance, E2E & Release | Week 5 (Days 21–25) | `Planned` | 0% | QA / Release Eng | B8 (Account Deletion) |

---

## 2. Detailed Work Breakdown by Phase

---

### Phase 0: Scaffolding, Tooling & API Contract Foundation

> **Target**: Week 1, Days 1–3  
> **Theme**: Infrastructure, Multi-Module Gradle, CI, and OpenAPI Model Generation  
> **Objective**: Stand up a compile-ready, multi-module Android project following Google's "Now in Android" architecture, wired to CI and generating Kotlin models from the backend OpenAPI schema.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P0-01` | Project Root | Initialize `/android` directory, Gradle 8.x wrapper, and version catalog with Kotlin 2.x and Compose BOM. | `/android/gradle/libs.versions.toml`, `/android/build.gradle.kts`, `/android/settings.gradle.kts` | `./gradlew --version` | `[x]` |
| `DEV-P0-02` | `build-logic` | Create custom convention plugins: `android-library`, `android-feature`, `compose`, `hilt`, `room`, `detekt`, `spotless`. | `/android/build-logic/convention/...` | Convention plugins compile cleanly | `[x]` |
| `DEV-P0-03` | Core Modules Setup | Initialize multi-module skeleton: `:core:model`, `:core:network`, `:core:auth`, `:core:database`, `:core:data`, `:core:designsystem`, `:core:ui`, `:core:notifications`, `:core:testing`. | Each module's `build.gradle.kts` and directory structure | `:app` builds with all core dependencies | `[x]` |
| `DEV-P0-04` | Feature Modules Setup | Initialize feature modules: `:feature:auth`, `:feature:home`, `:feature:intake`, `:feature:tickets`, `:feature:escalation`, `:feature:work`, `:feature:review`, `:feature:team`, `:feature:approvals`, `:feature:insights`, `:feature:notifications`, `:feature:help`, `:feature:profile`. | Feature module skeletons | Gradle project sync | `[x]` |
| `DEV-P0-05` | `:core:model` | Define core domain entities and enums (`Ticket`, `TicketStatus`, `Priority`, `Category`, `Prediction`, `Escalation`, `EscalationEligibility`, `Member`, `Team`, `Role`, `AllowedAction`). | `core/model/src/main/kotlin/com/routedesk/model/...` | Unit tests for domain models | `[x]` |
| `DEV-P0-06` | `:core:network` | Configure `openapi-generator-cli` Gradle task to compile backend `openapi.json` into typed DTOs with `kotlinx.serialization`. | `core/network/src/main/kotlin/.../dto/...`, `OpenApiGeneratorTask.kt` | DTO generation task completes with zero serialization warnings | `[x]` |
| `DEV-P0-07` | `:core:network` | Implement `ApiError` parser for `{code, message, field, details, request_id}` and setup Retrofit client with logging and user-agent interceptors. | `ApiClient.kt`, `ApiError.kt`, `NetworkInterceptors.kt` | Unit tests verifying error parsing against backend schemas | `[x]` |
| `DEV-P0-08` | `:core:testing` | Setup MockWebServer dispatcher and static JSON fixtures mirroring PRD sample tickets and escalations. | `TestFixtures.kt`, `MockResponseDispatcher.kt` | MockWebServer returns valid sample payloads | `[x]` |
| `DEV-P0-09` | CI Pipeline | Create GitHub Actions workflow `android-ci.yml` running Detekt, Spotless, Lint, unit tests, and assembleDebug. | `.github/workflows/android-ci.yml` | Green GitHub Actions run on initial PR | `[x]` |

#### Phase 0 Deliverables
- Fully working multi-module Gradle project compiling on Kotlin 2.x and Compose BOM.
- Automated OpenAPI code generation producing typed DTOs.
- Green CI check on GitHub Actions.

#### Phase 0 Exit Gate
- [x] `./gradlew :core:model:test :core:network:test` passes without errors.
- [x] Backend contract test confirms generated Kotlin DTOs match current FastAPI `openapi.json`.

---

### Phase 1: Design System Primitives & Token Authentication

> **Target**: Week 1, Days 3–5  
> **Theme**: Brand Aesthetics, Design System Primitives, Secure Storage, and Auth Lifecycle  
> **Objective**: Deliver a pixel-perfect design system matching references 1 & 4, and implement rotating token authentication with Keystore encryption.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P1-01` | `:core:designsystem` | Define color tokens (`Brand`: Nero `#171717`, Concrete `#594542`, Orange `#FD5323`, San `#EEE2D8`; `Neutral`: Paper `#F8F2ED`, Ink `#360A00`; `Semantic`: Danger, Attention, Warning, Success, Model). | `Color.kt`, `Theme.kt`, `ColorTokens.kt` | Compose Previews & Roborazzi screenshot tests | `[x]` |
| `DEV-P1-02` | `:core:designsystem` | Embed Chakra Petch (Light 300, Regular 400, SemiBold 600) and JetBrains Mono 400; configure Material 3 `Typography` scales with tabular figures (`tnum`). | `Type.kt`, `res/font/chakra_petch_*.ttf`, `res/font/jetbrains_mono_*.ttf` | Type scaling inspection (1.0x and 2.0x) | `[x]` |
| `DEV-P1-03` | `:core:designsystem` | Implement shape tokens (10dp, 16dp, 24dp, pill) and ink-tinted soft elevation shadows. | `Shape.kt`, `Elevation.kt` | UI component shadow rendering | `[x]` |
| `DEV-P1-04` | `:core:designsystem` | Build foundational UI primitives: `RdButton` (Primary, Accent, Secondary, Link, Loading state), `RdIconButton`, `RdFab`, `RdChip`, `RdCard`, `RdTile`, `RdListRow`. | `RdButton.kt`, `RdChip.kt`, `RdCard.kt`, `RdListRow.kt` | Interactive Previews for every state | `[x]` |
| `DEV-P1-05` | `:core:designsystem` | Build form and layout primitives: `RdTextField` (San/Nero800 background, 2dp Orange focus ring, counter), `RdSheet` (radius 24 top, drag handle), `RdTopBar`, `RdBottomBar` (floating 5-slot pill bar). | `RdTextField.kt`, `RdSheet.kt`, `RdTopBar.kt`, `RdBottomBar.kt` | Edge-to-edge & IME padding validation | `[x]` |
| `DEV-P1-06` | `:core:designsystem` | Build decorative canvas elements: `HatchedDivider`, `CropFrame`, `RdSkeleton` shimmer. | `CanvasDecorations.kt`, `RdSkeleton.kt` | Canvas rendering tests | `[x]` |
| `DEV-P1-07` | `:core:auth` | Implement Keystore + Google Tink AEAD encrypted refresh token store in Proto DataStore; implement in-memory `AccessTokenHolder` with 15-min TTL. | `TokenStore.kt`, `KeystoreEncryptor.kt`, `SessionManager.kt` | Unit tests for encryption, decryption, and token revocation | `[x]` |
| `DEV-P1-08` | `:core:auth` | Implement OkHttp `Authenticator` interceptor: automatically handles 401 via `POST /auth/refresh`, rotates token pair, and retries original request; forces sign-out if refresh fails. | `TokenAuthenticator.kt`, `AuthInterceptor.kt` | MockWebServer 401 retry test suite | `[x]` |
| `DEV-P1-09` | `:feature:auth` | Build Splash screen (`core-splashscreen` API) and 3-page swipeable Onboarding carousel (reference 7) with live stats strip calling `GET /kpis/public`. | `SplashScreen.kt`, `OnboardingScreen.kt`, `OnboardingViewModel.kt` | Screen flow preview & TalkBack pass | `[x]` |
| `DEV-P1-10` | `:feature:auth` | Build Sign In & Sign Up screen (reference 1): collapsible hero card, email/password validation, "Forgot Password", lockout alert, and **Demo Role Picker Sheet** (Requester, Agent, Engineer, Lead, Approver, Manager). | `SignInScreen.kt`, `SignUpScreen.kt`, `DemoRolePickerSheet.kt`, `AuthViewModel.kt` | Roborazzi screenshot test; demo login verification | `[x]` |
| `DEV-P1-11` | `:feature:auth` | Build Cold Start banner: triggers non-blocking `/health` ping on launch and shows "Waking up server..." message if latency > 5s. | `ColdStartBanner.kt`, `HealthMonitor.kt` | Delayed response unit test | `[x]` |

#### Phase 1 Deliverables
- Reusable Design System library with full `@Preview` catalog and Roborazzi golden snapshots.
- Secure Auth module with rotating refresh tokens and automatic 401 recovery.
- Functional Splash, Onboarding, Sign-in, Sign-up, and Demo Role Login screens.

#### Phase 1 Exit Gate
- [x] User can sign in using Demo Role Picker and tokens persist securely across app process death.
- [x] Token rotation on 401 and session clearing verified with unit tests.

---

### Phase 2: Requester Flow, Real-Time Predictions & Offline Outbox

> **Target**: Week 2 (Days 6–10)  
> **Theme**: Intake Flow, ML Prediction Feedback Loop, Room Outbox, and Ticket Lifecycle  
> **Objective**: Implement the full requester experience from ticket creation with instant ML prediction to offline queuing, SLA countdowns, and conversation threads.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P2-01` | `:feature:home` | Build Requester Home dashboard: status dot banner (healthy vs degraded mode), greeting header, bell icon with unread badge, 4 quick help tiles, horizontal open tickets carousel, and "Waiting on you" urgent rows. | `RequesterHomeScreen.kt`, `HomeViewModel.kt`, `HomeUiState.kt` | Compose UI test; pull-to-refresh test | `[x]` |
| `DEV-P2-02` | `:feature:intake` | Build Dual-Mode Intake container with segmented control (**Chat Intake** vs **Form Intake**). | `IntakeContainerScreen.kt`, `IntakeViewModel.kt` | Mode switching preview | `[x]` |
| `DEV-P2-03` | `:feature:intake` | Implement Chat Intake: conversational message bubbles, typing indicator, single call to `POST /predict` on message completion, and audio dictation hook. | `ChatIntakeView.kt`, `ChatBubble.kt`, `SpeechInputManager.kt` | Interactive chat simulation | `[x]` |
| `DEV-P2-04` | `:feature:intake` | Implement Prediction Card: displays predicted Category, Confidence bar, Priority chip, with **"Looks right"** and **"Not quite"** actions. | `PredictionCard.kt`, `PredictionPanel.kt` | UI test for confidence levels | `[x]` |
| `DEV-P2-05` | `:feature:intake` | Implement "Not quite" feedback sheet: category override picker (top 3 + full list) sending `POST /feedback` on ticket creation. | `CategoryOverrideSheet.kt` | Feedback payload verification | `[x]` |
| `DEV-P2-06` | `:feature:intake` | Implement FAQ deflection rows: shows top 3 matching FAQ articles with "Did this fix it?" deflection confirmation. | `FaqDeflectionView.kt`, `FaqItem.kt` | Deflection action flow test | `[x]` |
| `DEV-P2-07` | `:feature:intake` | Implement Form Intake: Subject input, 5,000-char Description counter, `blocking_team` toggle switch. | `FormIntakeView.kt` | Form validation and error states test | `[x]` |
| `DEV-P2-08` | `:feature:intake` | Build Ticket Confirmation Screen: slide-up card rendering Ticket ID (mono font), assigned Engineer, Team avatar, First Response SLA, and Expected Resolution time (< 5s target). | `TicketConfirmationScreen.kt` | Roborazzi screenshot test; latency measurement | `[x]` |
| `DEV-P2-09` | `:core:database` | Implement Room database entities: `TicketEntity`, `MessageEntity`, `NotificationEntity`, and `OutboxEntity`. | `AppDatabase.kt`, `TicketDao.kt`, `OutboxDao.kt` | Room Migration & DAO in-memory tests | `[x]` |
| `DEV-P2-10` | `:core:data` | Build WorkManager `OutboxSyncWorker`: monitors network state, drains queued `POST /tickets` and `POST /tickets/{id}/messages` with client UUID `Idempotency-Key` and exponential backoff. | `OutboxSyncWorker.kt`, `OfflineRepository.kt` | WorkManager test runner offline/online toggle test | `[x]` |
| `DEV-P2-11` | `:core:data` | Implement `ClockOffset` manager: parses HTTP `Date` response header to eliminate local device clock drift; drive shared `tickerFlow(1 s)`. | `ClockOffsetManager.kt`, `SlaTicker.kt` | Unit tests for clock skew correction | `[x]` |
| `DEV-P2-12` | `:feature:tickets` | Build My Tickets screen: Paging 3 list with Open, Waiting on me, and Resolved tabs, search filter, and category filter chips. | `MyTicketsScreen.kt`, `MyTicketsViewModel.kt` | Paging 3 RemoteMediator integration test | `[x]` |
| `DEV-P2-13` | `:feature:tickets` | Build Ticket Detail Screen: compact `StatusStepper`, `SlaTimer`, sticky assignee summary card, ETA change history modal, and action bar. | `TicketDetailScreen.kt`, `TicketDetailViewModel.kt`, `SlaTimer.kt` | Live countdown UI verification | `[x]` |
| `DEV-P2-14` | `:feature:tickets` | Build Conversation & Activity Tabs: message bubbles, system events, composer with offline draft support; Activity timeline and Escalation ladder. | `ConversationTab.kt`, `ActivityTab.kt`, `EscalationLadder.kt` | Message post offline queueing test | `[x]` |
| `DEV-P2-15` | `:feature:tickets` | Build Resolution Actions: "Confirm resolution" (`POST /confirm`) and "Reopen ticket" (`POST /reopen`) with mandatory reason sheet. | `ReopenReasonSheet.kt`, `ResolutionBanner.kt` | State transition test | `[x]` |

#### Phase 2 Deliverables
- Fully functional Requester Home, Ticket Intake (Chat & Form), Confirmation, and Detail screens.
- Robust Room database with WorkManager outbox for offline ticket and message queuing.
- Live SLA countdown engine synchronized to server time.

#### Phase 2 Exit Gate
- [x] Ticket created offline in airplane mode automatically submits and displays in My Tickets within 5 seconds of reconnecting.
- [x] Chat intake calls `/predict`, shows prediction card, and submits feedback on "Not quite".

---

### Phase 3: Push Notifications, Escalations & Inbox

> **Target**: Week 3 (Days 11–15)  
> **Theme**: Real-Time Alerts, Escalation Workflows, Deep Linking, and Notification Hub  
> **Objective**: Deliver push-to-action capabilities for urgent escalations and approvals via FCM HTTP v1, App Link routing, and in-app notification center.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P3-01` | `:core:notifications`| Implement `FirebaseMessagingService` processing **data-only** FCM messages; register and deregister device via `POST /devices` and `DELETE /devices/{id}`. | `RouteDeskFcmService.kt`, `DeviceRegistrationWorker.kt` | FCM token registration unit test | `[ ]` |
| `DEV-P3-02` | `:core:notifications`| Configure 5 Android Notification Channels: `escalations` (High importance), `approvals` (High), `sla` (High for staff), `ticket_updates` (Default), `system` (Low). | `NotificationChannelManager.kt` | Channel creation inspection on API 26+ | `[ ]` |
| `DEV-P3-03` | `:core:notifications`| Build secure Notification builder: enforce `VISIBILITY_PRIVATE` on lock screens; implement ticket notification grouping (`setGroup("ticket-T-{id}")`) with summaries. | `NotificationBuilder.kt` | Lock screen privacy test on emulator | `[ ]` |
| `DEV-P3-04` | `:feature:escalation` | Build Escalation Intake Sheet (reference 6): Ticket context card, `MemberPicker` sheet (`GET /directory/members?for_ticket={id}`), Reason choice chips, Note field (10–500 chars), and Response Preview card. | `EscalationSheet.kt`, `EscalationViewModel.kt` | Compose UI validation for form rules | `[ ]` |
| `DEV-P3-05` | `:feature:escalation` | Build `MemberPicker` component: suggested members pinned first (Lead/SD Manager); disable self, current owner, and members on leave (with one-tap delegate selection). | `MemberPickerSheet.kt`, `MemberRow.kt` | UI test for disabled state rules | `[ ]` |
| `DEV-P3-06` | `:feature:escalation` | Enforce Escalation Guardrails: disable Escalate button when server returns `ESCALATION_COOLDOWN` or `ESCALATION_RATE_LIMIT` with exact countdown time. | `EscalationGuardrailView.kt` | Guardrail error handling test | `[ ]` |
| `DEV-P3-07` | `:feature:escalation` | Build Respond to Escalation Screen: live countdown header to response deadline (30 min Critical, 2 hr standard), ticket summary, reason note. | `RespondEscalationScreen.kt`, `RespondViewModel.kt` | Deadline timer countdown test | `[ ]` |
| `DEV-P3-08` | `:feature:escalation` | Implement 3 Escalation Actions: **Accept** (mandatory new ETA sheet), **Reassign** (`MemberPicker` + new ETA), **Decline** (mandatory decline reason). | `AcceptEtaSheet.kt`, `DeclineReasonSheet.kt` | Concurrency test for `ESCALATION_ALREADY_RESPONDED` | `[ ]` |
| `DEV-P3-09` | `:app` | Configure Android App Links in `AndroidManifest.xml` for `https://<host>/app/tickets/{id}` and `https://<host>/escalations/{id}`; implement signed-out intent interception. | `AndroidManifest.xml`, `DeepLinkHandlerActivity.kt` | `adb shell am start -a android.intent.action.VIEW -d "..."` | `[ ]` |
| `DEV-P3-10` | `:feature:notifications` | Build Notification Inbox Screen: grouped by date, unread indicator dot, "Mark all read" (`POST /notifications/read-all`), deep-link navigation on tap. | `NotificationInboxScreen.kt`, `NotificationViewModel.kt` | Inbox list interaction test | `[ ]` |
| `DEV-P3-11` | `:core:notifications`| Build 15-minute fallback background sync worker for notifications when Google Play services are missing or permission is denied. | `NotificationSyncWorker.kt` | Fallback worker execution test | `[ ]` |

#### Phase 3 Deliverables
- End-to-end FCM push notification pipeline with 5 system channels.
- Full Escalation intake sheet with guardrails and delegate selection.
- Respond to Escalation screen with deadline countdown and 3 primary actions.
- App Links handling for direct deep linking from push notifications.

#### Phase 3 Exit Gate
- [ ] Escalation push notification received on device wakes screen, shows private content on lock screen, and tap opens Respond to Escalation directly.
- [ ] Concurrency conflict `ESCALATION_ALREADY_RESPONDED` displays who handled it and disables actions.

---

### Phase 4: Staff Workspaces & Role-Based Actions

> **Target**: Week 4 (Days 16–20)  
> **Theme**: Role Command Centers, SLA Queue Management, Approvals, Triage & Manager Insights  
> **Objective**: Implement tailored workspaces for Engineer, Team Lead, Approver, Service Desk Agent, and IT Manager roles, driven strictly by server `allowed_actions`.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P4-01` | `:feature:work` | Build Engineer Workspace (My Queue): SLA risk counter tiles (Open, Due today, At risk, Breached), list sorted by SLA urgency, side-state badges. | `EngineerQueueScreen.kt`, `EngineerQueueViewModel.kt` | Queue sorting & filter test | `[ ]` |
| `DEV-P4-02` | `:feature:work` | Build Staff Ticket Actions bar strictly driven by server `allowed_actions`: Update status, Change ETA, Request info, Hand back, and Internal note toggle. | `StaffActionBar.kt`, `StaffTicketScreen.kt` | Action permission matrix test | `[ ]` |
| `DEV-P4-03` | `:feature:work` | Build Change ETA Sheet (reference 6 style): Date and time pickers in business hours, mandatory reason dropdown, preview card ("Requester will be notified"). | `ChangeEtaSheet.kt` | Business hours validation test | `[ ]` |
| `DEV-P4-04` | `:feature:work` | Build Request Info & Hand Back Sheets: Request info moves ticket to Waiting on Requester; Hand back prompts for reason. | `RequestInfoSheet.kt`, `HandBackSheet.kt` | SLA pause validation test | `[ ]` |
| `DEV-P4-05` | `:feature:work` | Implement Optimistic Concurrency Handler: Send `version` with mutations; handle `STALE_VERSION` (409) by keeping form open and displaying update banner. | `VersionConflictHandler.kt` | Simulated stale version retry test | `[ ]` |
| `DEV-P4-06` | `:feature:approvals` | Build Approver Pending List: Category chip, requester info, purchase justification snippet, and 1-business-day response timer. | `ApproverQueueScreen.kt`, `ApproverViewModel.kt` | Approver queue UI test | `[ ]` |
| `DEV-P4-07` | `:feature:approvals` | Build Approver Decide Screen: Full justification card, requester details, one-tap **Approve** (optional note) and **Reject** (mandatory reason). | `ApprovalDecideScreen.kt` | Approval submission test | `[ ]` |
| `DEV-P4-08` | `:feature:team` | Build Team Lead Dashboard: SLA warnings list (>75% time used), team tickets grouped by status, Reassign action with `MemberPicker`. | `TeamLeadScreen.kt`, `TeamLeadViewModel.kt` | Team ticket grouping test | `[ ]` |
| `DEV-P4-09` | `:feature:team` | Build Team Availability & Workload Radar: View member active tickets, shift status, skills, and search "Who can take this now?". | `TeamAvailabilityScreen.kt`, `WorkloadBar.kt` | Availability roster rendering test | `[ ]` |
| `DEV-P4-10` | `:feature:review` | Build Service Desk Agent Review Queue: Confidence score bar, reason badges (`low_confidence`, `multi_issue`), countdown to 30-min SLA promise. | `AgentReviewScreen.kt`, `AgentReviewViewModel.kt` | Card swipe-to-accept test | `[ ]` |
| `DEV-P4-11` | `:feature:review` | Build Agent Triage Screen: Top 3 predicted categories, category/priority override pickers, assignment suggestion engine (`GET /assignment-suggestion`). | `AgentTriageScreen.kt` | Assignment engine pick test | `[ ]` |
| `DEV-P4-12` | `:feature:insights` | Build Manager Insights Screen: Date range selector (Today, 7d, 30d), 8 numeric KPI tiles (auto-route rate, review accuracy, SLA compliance, MTTR, hours saved). | `ManagerInsightsScreen.kt`, `InsightsViewModel.kt`, `KpiTile.kt` | KPI calculation test | `[ ]` |
| `DEV-P4-13` | `:feature:insights` | Integrate Vico Compose Charts: Auto-route rate over time (line chart), SLA compliance by team (bar chart), Escalations by reason (bar chart). | `VicoCharts.kt`, `InsightsChartsView.kt` | Chart rendering & theme test | `[ ]` |
| `DEV-P4-14` | `:core:ui` | Build Ticket Attachment Uploader (Should - B6): Photo Picker (`PickVisualMedia`) and Camera contract (`TakePicture`) with client-side EXIF stripping; Coil 3 image viewer. | `AttachmentPicker.kt`, `ExifStripper.kt`, `AttachmentViewer.kt` | EXIF removal verification test | `[ ]` |

#### Phase 4 Deliverables
- Dedicated workspace screens for Engineer, Team Lead, Approver, Agent, and Manager roles.
- Optimistic locking implementation recovering gracefully from `STALE_VERSION`.
- Vico Compose charts for real-time KPI visualization.
- Attachment picker and previewer with EXIF sanitization.

#### Phase 4 Exit Gate
- [ ] Each demo role signs in and lands directly on their dedicated workspace.
- [ ] Approver receives push, unlocks, and executes one-tap approval within 5 seconds.

---

### Phase 5: Hardening, Polish, Security & Release Readiness

> **Target**: Week 5 (Days 21–25)  
> **Theme**: Security Audits, WCAG Accessibility, Performance Profiles, Maestro E2E, and Release Distribution  
> **Objective**: Harden the application against OWASP MASVS L1, optimize startup and memory footprints, verify automated end-to-end flows, and distribute release candidates.

#### Task Matrix

| Task ID | Component / Module | Task Description | Deliverable Files | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `DEV-P5-01` | `:core:auth` | Implement Biometric Gate (`androidx.biometric`): Default ON for staff roles; prompt on launch and after >5 min backgrounded. | `BiometricPromptManager.kt`, `BiometricLockActivity.kt` | Biometric timeout and fallback test | `[ ]` |
| `DEV-P5-02` | `:feature:profile` | Build Settings & Account Deletion: Notification channel shortcuts, biometric toggle, "Delete My Account" flow (`DELETE /auth/me`) complying with Google Play policy. | `SettingsScreen.kt`, `AccountDeletionDialog.kt` | Account deletion verification | `[ ]` |
| `DEV-P5-03` | `:feature:help` | Build Help & FAQ Screen: Search bar, 8 category chips, expandable `FaqItem` accordions; bundle static offline fallback in `assets/faq.json`. | `FaqScreen.kt`, `assets/faq.json`, `FaqViewModel.kt` | Offline FAQ browsing test | `[ ]` |
| `DEV-P5-04` | Security | Implement OWASP MASVS L1 controls: `FLAG_SECURE` on password screens, strict `network_security_config.xml`, user-id rate limit keys, zero PII in Crashlytics. | `network_security_config.xml`, `CrashlyticsSanitizer.kt` | Security static analysis scan | `[ ]` |
| `DEV-P5-05` | Accessibility | WCAG 2.2 AA audit: 48dp minimum touch targets, 200% font scaling reflow checks, TalkBack content descriptions and merged `TicketCard` audio semantics. | `AccessibilityModifiers.kt`, `res/values/strings.xml` | Accessibility Scanner & TalkBack manual pass | `[ ]` |
| `DEV-P5-06` | `:benchmark` | Generate Baseline Profiles using Macrobenchmark to guarantee cold start < 1.5s; configure R8 full mode shrinking to meet < 12 MB APK size limit. | `BaselineProfileGenerator.kt`, `benchmark/build.gradle.kts` | Macrobenchmark startup timing report | `[ ]` |
| `DEV-P5-07` | E2E Testing | Build automated Maestro flows: Requester Intake (`flow_1.yaml`), Escalation Lifecycle (`flow_2.yaml`), Engineer Triage (`flow_3.yaml`), and Offline Outbox (`flow_4.yaml`). | `/android/maestro/*.yaml` | `maestro test /android/maestro` green run | `[ ]` |
| `DEV-P5-08` | Release CI/CD | Build `android-release.yml`: Automated build of signed release AAB/APK using GitHub Secrets keystore; upload mapping file to Crashlytics; deploy to Firebase App Distribution. | `.github/workflows/android-release.yml` | Successful App Distribution release | `[ ]` |
| `DEV-P5-09` | Play Store Readiness| Prepare store assets: 512px icon, feature graphic, localized screenshots, Data Safety declaration, and privacy policy URL. | `/android/fastlane/metadata/...` | Play Console pre-launch report pass | `[ ]` |

#### Phase 5 Deliverables
- Biometric security gate and compliant account deletion workflow.
- Baseline Profiles compiled into production AAB yielding < 1.5s cold start and < 12 MB download size.
- 100% automated Maestro E2E test suite passing against staging.
- Signed production build deployed via Firebase App Distribution.

#### Phase 5 Exit Gate
- [ ] Cold start < 1.5s on mid-range physical device; APK size < 12 MB; zero ANRs.
- [ ] All 4 Maestro E2E flows execute to completion on staging environment.

---

## 3. PRD Feature & Screen Traceability Matrix

This table maps every PRD functional requirement and screen mockup directly to its development phase and implementing task.

| PRD Requirement / Screen | Target Audience | Implementing Phase | Primary Task IDs | Deliverable Summary |
| :--- | :--- | :---: | :--- | :--- |
| **FR-1..3 (ML Prediction)** | Requester, Agent | Phase 2 | `DEV-P2-03`, `DEV-P2-04` | Category & priority prediction card with confidence bar |
| **FR-12 (Prediction Feedback)**| Requester, Agent | Phase 2 | `DEV-P2-05`, `DEV-P4-11` | "Not quite" feedback picker and triage corrections |
| **PRD 3.3 (5s Confirmation)** | Requester | Phase 2 | `DEV-P2-08` | Full confirmation card with owner and SLA in < 5s |
| **PRD 4B.1 (Requester Intake)** | Requester | Phase 2 | `DEV-P2-02`, `DEV-P2-07` | Dual-mode Chat and Form intake with FAQ deflection |
| **FR-20 (Assignment Suggestion)**| Agent, Team Lead | Phase 4 | `DEV-P4-08`, `DEV-P4-11` | Member picker with suggestion algorithm recommendations |
| **FR-21, 22 (ETA Management)** | Engineer, Requester| Phase 2, 4 | `DEV-P2-13`, `DEV-P4-03` | Change ETA sheet with mandatory reasons & change history |
| **FR-23 (Activity Timeline)** | All Roles | Phase 2 | `DEV-P2-14` | Chronological audit events and status transitions |
| **FR-24 (SLA Ladder Countdown)**| All Roles | Phase 2 | `DEV-P2-11`, `DEV-P2-13` | Live `SlaTimer` with clock skew compensation and color coding |
| **FR-25, 26 (Escalation Sheet)**| Requester | Phase 3 | `DEV-P3-04`, `DEV-P3-06` | Reference 6 escalation sheet with cooldown guardrails |
| **FR-27 (Respond to Escalation)**| Chosen Member | Phase 3 | `DEV-P3-07`, `DEV-P3-08` | Urgent deadline countdown; Accept, Reassign, Decline actions |
| **FR-28 (Staff Audit View)** | Staff Roles | Phase 4 | `DEV-P4-02` | Internal notes and staff audit history on ticket detail |
| **FR-29 (Wrong-Team Feedback)** | Requester, Lead | Phase 3 | `DEV-P3-04` | "Wrong team" feedback flag to retrain routing models |
| **FR-30 (Approvals Queue)** | Approver | Phase 4 | `DEV-P4-06`, `DEV-P4-07` | Pending approval cards and one-tap decide screen |
| **FR-31 (Manager KPIs)** | SD / IT Manager | Phase 4 | `DEV-P4-12`, `DEV-P4-13` | 8 KPI tiles and Vico interactive trend charts |
| **Reference 1 (Sign-In/Auth)** | All Roles | Phase 1 | `DEV-P1-10` | Collapsible hero card, demo role login sheet |
| **Reference 4 (Mobile Dashboard)**| All Roles | Phase 2, 4 | `DEV-P2-01`, `DEV-P4-01` | Floating 5-slot bottom bar, quick action tiles, ticket carousel |
| **Reference 5 (Chat & FAQ)** | Requester | Phase 2, 5 | `DEV-P2-03`, `DEV-P5-03` | Conversational ticket intake and offline FAQ accordions |
| **Reference 6 (Automation Sheet)**| Staff, Requester | Phase 3, 4 | `DEV-P3-04`, `DEV-P4-03` | Preview card, designated member picker, reason chips |

---

## 4. Backend Synchronization & Mock Fallback Matrix

This matrix ensures mobile engineers can develop continuously even if backend items are delayed.

| Backend Item | Priority | Target Week | Live Endpoint | Mock / Local Fallback Strategy |
| :--- | :---: | :---: | :--- | :--- |
| **B1: Token Auth** | Must | Week 1 | `POST /auth/token`, `/refresh`, `/demo-token` | OkHttp cookie interceptor using existing web cookie session. |
| **B9: App Config** | Must | Week 1 | `GET /app-config` | Mock JSON in `:core:testing` with `min_version=1`, `status="ok"`. |
| **B7: Asset Links** | Must | Week 1 | `/.well-known/assetlinks.json` | Test via custom URI scheme `routedesk://app/...` in debug builds. |
| **B4: Mobile Channel** | Must | Week 2 | `TicketCreateIn.channel = "android"` | Omit field during local dev; defaults to `"portal"`. |
| **B5: Idempotency Key** | Must | Week 2 | `POST /tickets/{id}/messages` header | MockWebServer simulates 200 on duplicate idempotency key retries. |
| **B2: Device Registry** | Must | Week 3 | `POST /devices`, `DELETE /devices/{id}` | Local stub repository saving token in Room without network call. |
| **B3: Push Outbox** | Must | Week 3 | FCM HTTP v1 Dispatcher | Send test FCM payloads via Firebase Console or `/internal/push/test`. |
| **B6: Attachments** | Should | Week 4 | `POST /tickets/{id}/attachments` | Store file locally in app cache; render via Coil from local URI. |
| **B8: Account Deletion**| Must (Play)| Week 5 | `DELETE /auth/me` | Clear local database and navigate to Sign-In screen. |
| **B10: Weak ETags** | Could | Week 5 | `ETag` on `GET /tickets/{id}` | Standard HTTP 200 payload parsing without 304 handling. |

---

## 5. Definition of Done (DoD) Checklist per Phase

To mark any phase as `Complete`, all of the following quality gates must be satisfied:

```markdown
- [ ] Code compiles with Kotlin 2.x and K2 compiler plugin with zero warnings.
- [ ] Detekt, ktlint, and Spotless pass with zero violations.
- [ ] Android Lint passes on release variant with zero high-severity issues.
- [ ] Unit & ViewModel test coverage exceeds 80% on changed files.
- [ ] All interactive Composables have @Preview in Light and Dark themes.
- [ ] Roborazzi visual regression tests pass for 360dp and 430dp widths at 100% and 200% font scales.
- [ ] Offline resilience validated: app handles sudden network loss without crashing or dropping user drafts.
- [ ] Cold start and memory leaks verified via Android Studio Profiler and LeakCanary (debug).
- [ ] PR reviewed, approved, and merged to main with passing GitHub Actions workflow.
```
