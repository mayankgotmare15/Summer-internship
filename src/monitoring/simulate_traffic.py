"""
Traffic Simulator for IT Support Ticket API.
Simulates production traffic including normal requests, vocabulary shift drift,
and emergent unseen category drift (e.g. held-out Storage tickets).
"""

import time

import requests

API_URL = "http://127.0.0.1:8000"

NORMAL_SAMPLES = [
    "Unable to connect to company VPN from home network.",
    "Need password reset for my domain user account.",
    "Requesting admin rights to install developer IDE.",
    "Laptop trackpad is not responding and battery running hot.",
    "How to download W-2 and tax forms from payroll portal?",
    "Need quotation approval for 3 software licenses.",
    "Creating new GitLab repository for internal sprint.",
]

DRIFT_VOCABULARY_SAMPLES = [
    "Quantum compute cluster GPU nodes experiencing PCIe kernel panic.",
    "Kubernetes ingress controller ingress-nginx TLS handshake timeout.",
    "Terraform state lock acquisition failed on DynamoDB table.",
    "ArgoCD application sync status is Degraded with Helm chart error.",
    "Istio service mesh envoy proxy 503 upstream connection termination.",
]

HELD_OUT_CATEGORY_SAMPLES = [
    "Shared network drive full, cannot save project files since morning.",
    "Requesting 500GB additional storage quota on NAS volume floor 2.",
    "Increase AWS S3 bucket quota for model training artifacts repository.",
    "Backup recovery request for deleted directory on file server.",
    "Disk space critical warning on server /var/log partition 100% full.",
]


def send_ticket(text: str, ticket_id: str):
    try:
        resp = requests.post(
            f"{API_URL}/predict", json={"text": text, "ticket_id": ticket_id}, timeout=3
        )
        if resp.status_code == 200:
            res = resp.json()
            print(
                f"[{res['decision'].upper()}] {ticket_id} -> {res['category']} ({res['category_confidence']:.2f})",
                flush=True,
            )
        else:
            print(f"Error {resp.status_code} for {ticket_id}", flush=True)
    except Exception as e:
        print(f"Failed to send {ticket_id}: {e}", flush=True)


def run_traffic_simulation(mode: str = "all"):
    print(f"Starting traffic simulation in mode: {mode}...")

    # Batch 1: In-Distribution Traffic
    if mode in ["all", "normal"]:
        print("\n--- Sending In-Distribution Normal Traffic ---")
        for i, text in enumerate(NORMAL_SAMPLES * 3):
            send_ticket(text, f"sim-normal-{i + 1:03d}")
            time.sleep(0.05)

    # Batch 2: Vocabulary Shift
    if mode in ["all", "drift"]:
        print("\n--- Sending Vocabulary Shift Traffic ---")
        for i, text in enumerate(DRIFT_VOCABULARY_SAMPLES * 2):
            send_ticket(text, f"sim-drift-vocab-{i + 1:03d}")
            time.sleep(0.05)

    # Batch 3: Held-out Unseen Category Drift
    if mode in ["all", "drift"]:
        print("\n--- Sending Emergent Category Drift (Storage) Traffic ---")
        for i, text in enumerate(HELD_OUT_CATEGORY_SAMPLES * 3):
            send_ticket(text, f"sim-drift-cat-{i + 1:03d}")
            time.sleep(0.05)

    print(
        "\nTraffic simulation batch complete. Logs written to data/monitoring/prediction_log.jsonl"
    )


if __name__ == "__main__":
    run_traffic_simulation()
