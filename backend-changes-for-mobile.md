# Backend Changes the Android App Needs

For the thread that owns the [production design](../architecture/README.md). This file does not edit the architecture docs; it lists what the [Android app plan](android-app-plan.md) needs from the API so the owner can fold it in. All items are additive: nothing the web app uses changes behaviour.

Estimated total: about 4 to 5 developer days, mostly in week M1 of the Android schedule (post-internship). B1 can be done during the internship if there is a spare half day; nothing else should be.

| # | Change | Priority | Effort |
| --- | --- | --- | --- |
| B1 | Token auth for native clients | Must | 1 day |
| B2 | Device registry for push | Must | 0.5 day |
| B3 | Push channel in the outbox (FCM HTTP v1) | Must | 1 day |
| B4 | `channel` value for Android tickets | Must | 15 min |
| B5 | Idempotency key on posting messages | Must | 1 hour |
| B6 | Ticket attachments | Should | 1 to 1.5 days |
| B7 | `/.well-known/assetlinks.json` for App Links | Must | 30 min |
| B8 | Account deletion | Must if published on Play | 0.5 day |
| B9 | `GET /app-config` (min version, status banner, flags) | Must | 1 hour |
| B10 | `ETag` on ticket detail and lists | Could | 0.5 day |
| B11 | Password reset (also missing for the web's "Forgot password?" link) | Should | 0.5 day |

---

## B1. Token auth for native clients

The web uses an httpOnly cookie with `SameSite=Lax` and an `X-Requested-With` header (backend design section 8). A native app could carry the cookie in OkHttp, but short-lived bearer tokens with refresh rotation are the safer, standard model for a phone that can be lost.

**New endpoints (identity module)**

| Method and path | Auth | Use case |
| --- | --- | --- |
| `POST /auth/token` | P | `issue_tokens(email, password, device_name)` → `{access_token, expires_in, refresh_token, me}` |
| `POST /auth/demo-token` | P (only `DEMO_MODE=true`) | same as `demo-login` but returns tokens |
| `POST /auth/refresh` | P (refresh token in body) | rotate: returns a new access and refresh token, marks the old refresh token used |
| `POST /auth/logout` (existing) | U | also accepts `{refresh_token}` and revokes it |
| `GET /auth/sessions`, `DELETE /auth/sessions/{id}` | U | list and revoke signed-in devices (web profile page can use it too) |

**Rules**

- Access token: same JWT claims as the cookie (`sub`, `role`, `team_id`), 15-minute expiry, sent as `Authorization: Bearer`.
- Refresh token: opaque 256-bit random value; only its SHA-256 hash is stored. 30-day expiry, rotated on every use. Reuse of an already-rotated token revokes the whole family (theft detection).
- `get_current_user` accepts **either** the cookie **or** the bearer header. The `X-Requested-With` CSRF check applies only to cookie-authenticated mutations; bearer requests are not CSRF-prone.
- Revoke all refresh tokens on password change, role change, deactivation and account deletion.
- Login rate limit and the 5-attempt lockout apply to `/auth/token` exactly as to `/auth/login`.

**New table**

| Table | Columns | Constraints |
| --- | --- | --- |
| `refresh_tokens` | id, user_id, family_id, token_hash, device_name, created_at, last_used_at, expires_at, revoked_at, replaced_by | `UNIQUE(token_hash)`, `INDEX(user_id, revoked_at)`; retention: delete 30 days after expiry |

## B2. Device registry for push

| Method and path | Auth | Use case |
| --- | --- | --- |
| `POST /devices` | U | upsert `{fcm_token, platform: "android", app_version, os_version, locale}` for the caller; returns `{id}` |
| `DELETE /devices/{id}` | U (own device) | on sign-out |

| Table | Columns | Constraints |
| --- | --- | --- |
| `devices` | id, user_id, platform, fcm_token, app_version, os_version, created_at, last_seen_at, disabled_at | `UNIQUE(fcm_token)` (a token moving to another user re-binds it), `INDEX(user_id)` |

## B3. Push channel in the outbox

- Add `push` to `outbox.channel` (`email`, `webhook`, `push`). When the notifications module writes an in-app notification for a user with active devices, it also writes one `push` outbox row per device in the same transaction (keeps the transactional-outbox guarantee).
- Dispatcher sends through **FCM HTTP v1** (`https://fcm.googleapis.com/v1/projects/{project}/messages:send`) using a Firebase service-account key held as a host secret (`FCM_SERVICE_ACCOUNT_JSON`). Free.
- Payload is a **data message** only: `{type, notification_id, ticket_id?, escalation_id?, title, body, channel_id}`. `title` and `body` come from the same templates as the in-app inbox, never include the ticket description, and truncate the subject to 40 characters.
- `channel_id` per event: `escalations`, `approvals`, `sla`, `ticket_updates`, `system` (Android plan 10.2). Set Android priority `high` for the first three so they wake a dozing phone.
- FCM `UNREGISTERED` or `INVALID_ARGUMENT` for a token → set `devices.disabled_at`; no retry. Other failures use the existing backoff.
- New events worth a push that may not yet create a notification row: escalation response deadline at 50% and 90% (for the chosen member), approval window at 75%. Both fit inside the existing SLA tick.
- Dev only: `POST /internal/push/test` (service token) to send a sample of each event type to one user.

## B4. Android channel on tickets

`TicketCreateIn.channel` gains `"android"` (today: `portal`, `chat`, `email_sim`). Stored on the ticket so KPIs can split web and mobile. No other change.

## B5. Idempotency on messages

`POST /tickets/{id}/messages` accepts an `Idempotency-Key` header, using the existing `idempotency_keys` table, so a message queued offline and retried is stored once. Same for `POST /tickets` (already designed).

## B6. Ticket attachments (Should)

Neither the web plan's attachment rows nor the Android photo picker has a backend yet.

| Method and path | Auth | Use case |
| --- | --- | --- |
| `POST /tickets/{id}/attachments` | owner requester or staff on the ticket | multipart upload; max 10 MB, images and PDF only (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`), max 5 per ticket |
| `GET /tickets/{id}/attachments/{att_id}` | same as ticket view | returns a short-lived signed URL or streams the file |

- Storage cannot be the container disk (wiped on redeploy). Default: **Cloudflare R2 or Supabase Storage free tier**, private bucket, signed URLs with 5-minute expiry.
- Table `attachments` (id, ticket_id, uploader_id, filename, content_type, size, storage_key, created_at).
- Strip EXIF location from images server-side; the Android app also strips it before upload.
- Attachments are never sent to the model.

## B7. App Links

Serve `GET /.well-known/assetlinks.json` from FastAPI (before the SPA catch-all) with the app's package name and the SHA-256 fingerprints of the release (Play App Signing) and debug keys, read from config so CD can update them without code changes. This lets `https://<host>/app/tickets/T-1042` open the app.

## B8. Account deletion (Play policy)

Apps that let people create accounts must let them delete them, in the app and through a web link.

- `DELETE /auth/me` (U, requires password re-entry or a recent login): requester accounts are deactivated, personal fields (name, email) are anonymised, refresh tokens and devices removed. Tickets stay for audit and KPIs but show "Deleted user".
- Staff accounts come from the roster and cannot self-delete; the endpoint returns `ACCOUNT_MANAGED_BY_ROSTER` (403) and the app explains who to contact.
- A public web page `/account/delete` explaining the process, for the Play listing.

## B9. App config

`GET /app-config` (public, cached 5 minutes):

```json
{
  "android": { "min_supported_version_code": 10, "latest_version_code": 14 },
  "status": { "level": "ok | degraded | incident", "message": "VPN degraded in Pune office" },
  "features": { "attachments": false, "chat_intake": true, "sso": false },
  "business_calendar": { "timezone": "Asia/Kolkata", "hours": "Mon-Fri 09:00-18:00" }
}
```

Values come from `app_settings` (editable through the existing `PUT /admin/config/{key}`), so the Streamlit console can set the status banner. The web home's status line can use the same endpoint.

## B10. ETags (Could)

Weak `ETag` from the ticket `version` on `GET /tickets/{id}`, and from the max `updated_at` on list pages; honour `If-None-Match` with 304. Cuts mobile data and speeds refresh.

## B11. Password reset (Should)

Both apps show "Forgot password?" but the identity module has no reset flow:

- `POST /auth/password-reset/request {email}` → always 202 (no account probing), emails a single-use link `https://<host>/reset?token=…` valid 30 minutes (the Android app opens it via App Link).
- `POST /auth/password-reset/confirm {token, new_password}` → sets the password and revokes all sessions (B1).
- Table `password_resets` (token_hash, user_id, expires_at, used_at).

---

## Things that need no change

- `/api/v1` paths, schemas, error codes, `allowed_actions`, `escalation_eligibility`, `sla_state`, cursor pagination and UTC timestamps all work for Android as designed.
- CORS: not needed for a native app.
- Rate limiting: key authenticated requests by user id rather than IP, since many phones share a carrier NAT address. If slowapi already keys by user for signed-in calls, nothing to do.
- The SLA tick and outbox jobs already run on the 15-minute GitHub cron when the host sleeps, which is what keeps push notifications flowing on a free tier.
