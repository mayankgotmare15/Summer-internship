package com.routedesk.testing

import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.RecordedRequest

class MockResponseDispatcher : Dispatcher() {

    override fun dispatch(request: RecordedRequest): MockResponse {
        val path = request.path ?: return MockResponse().setResponseCode(404)

        return when {
            path.startsWith("/auth/demo-token") || path.startsWith("/auth/token") -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.AUTH_TOKEN_SUCCESS)
            }

            path.startsWith("/auth/me") -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.USER_ME_REQUESTER)
            }

            path.startsWith("/predict") -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.PREDICT_ACCESS_HIGH)
            }

            path == "/tickets" && request.method == "POST" -> {
                MockResponse()
                    .setResponseCode(201)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.TICKET_CREATED_T1042)
            }

            path.startsWith("/tickets/T-1042") && request.method == "GET" -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.TICKET_DETAIL_T1042)
            }

            path.startsWith("/tickets") && request.method == "GET" -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody("[${TestFixtures.TICKET_DETAIL_T1042}]")
            }

            path.startsWith("/app-config") -> {
                MockResponse()
                    .setResponseCode(200)
                    .setHeader("Content-Type", "application/json")
                    .setBody(TestFixtures.APP_CONFIG_OK)
            }

            path.startsWith("/devices") -> {
                MockResponse().setResponseCode(200)
            }

            else -> MockResponse().setResponseCode(404).setBody("""{"code":"NOT_FOUND","message":"Path $path not mocked"}""")
        }
    }
}

object TestFixtures {

    val AUTH_TOKEN_SUCCESS = """
        {
          "access_token": "mock_jwt_access_token_12345",
          "expires_in": 900,
          "refresh_token": "mock_refresh_token_67890",
          "me": {
            "id": "usr_req_01",
            "email": "alex.chen@example.com",
            "name": "Alex Chen",
            "role": "requester",
            "department": "Engineering",
            "is_demo": true
          }
        }
    """.trimIndent()

    val USER_ME_REQUESTER = """
        {
          "id": "usr_req_01",
          "email": "alex.chen@example.com",
          "name": "Alex Chen",
          "role": "requester",
          "department": "Engineering",
          "is_demo": true
        }
    """.trimIndent()

    val PREDICT_ACCESS_HIGH = """
        {
          "category": "access",
          "category_confidence": 0.94,
          "top_categories": [
            { "category": "access", "score": 0.94 },
            { "category": "security", "score": 0.04 },
            { "category": "software", "score": 0.02 }
          ],
          "priority": "high",
          "priority_confidence": 0.88,
          "priority_source": "model",
          "decision": "auto_route",
          "routed_team": { "code": "access_id", "name": "Access and Identity Team" },
          "threshold": 0.70,
          "model_version": "v1.2",
          "prediction_id": "pred_98765",
          "latency_ms": 42,
          "top_keywords": ["vpn", "okta", "auth"]
        }
    """.trimIndent()

    val TICKET_CREATED_T1042 = """
        {
          "id": "T-1042",
          "ticket_uuid": "550e8400-e29b-41d4-a716-446655440000",
          "status": "assigned",
          "category": "access",
          "priority": "high",
          "decision": "auto_route",
          "assignee": {
            "id": "usr_eng_02",
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "role": "engineer"
          },
          "team": { "code": "access_id", "name": "Access and Identity Team" },
          "first_response_due": "2026-11-01T14:30:00Z",
          "resolution_due": "2026-11-01T18:00:00Z",
          "can_escalate": true
        }
    """.trimIndent()

    val TICKET_DETAIL_T1042 = """
        {
          "id": "T-1042",
          "ticket_uuid": "550e8400-e29b-41d4-a716-446655440000",
          "subject": "VPN connection drops every 10 minutes",
          "description": "Whenever I connect to the Pune office VPN, it drops constantly.",
          "category": "access",
          "priority": "high",
          "priority_source": "model",
          "status": "assigned",
          "decision": "auto_route",
          "team": { "code": "access_id", "name": "Access and Identity Team" },
          "assignee": {
            "id": "usr_eng_02",
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "role": "engineer"
          },
          "is_escalated": false,
          "escalation_level": "E1",
          "can_escalate": true,
          "escalation_eligibility": {
            "allowed": true,
            "used_last_24h": 0,
            "max_per_24h": 3
          },
          "allowed_actions": ["update_status", "change_eta", "request_info", "escalate"],
          "first_response_due": "2026-11-01T14:30:00Z",
          "resolution_due": "2026-11-01T18:00:00Z",
          "sla_state": "on_track",
          "used_pct": 25.0,
          "messages": [
            {
              "id": "msg_01",
              "author_id": "usr_req_01",
              "author_name": "Alex Chen",
              "kind": "public",
              "body": "Whenever I connect to the Pune office VPN, it drops constantly.",
              "created_at": "2026-11-01T10:00:00Z"
            }
          ],
          "version": 1,
          "created_at": "2026-11-01T10:00:00Z"
        }
    """.trimIndent()

    val APP_CONFIG_OK = """
        {
          "android": {
            "min_supported_version_code": 1,
            "latest_version_code": 1
          },
          "status": {
            "level": "ok",
            "message": "All systems operational"
          },
          "features": {
            "attachments": true,
            "chat_intake": true,
            "sso": false
          },
          "business_calendar": {
            "timezone": "Asia/Kolkata",
            "hours": "Mon-Fri 09:00-18:00"
          }
        }
    """.trimIndent()
}
