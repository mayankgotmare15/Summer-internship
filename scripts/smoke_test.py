"""Automated smoke test script for container and live deployment verification.

Verifies:
1. /health returns HTTP 200
2. /ready returns HTTP 200 with model ready
3. /api/v1/model-info returns champion model metadata
4. /api/v1/predict correctly infers category, priority, and routing action
"""

import argparse
import sys
import time

import httpx


def run_smoke_test(base_url: str, max_retries: int = 30, retry_delay: float = 1.0) -> bool:
    base_url = base_url.rstrip("/")
    print(f"Starting smoke tests against target: {base_url}")

    # 1. Poll /health
    health_url = f"{base_url}/health"
    healthy = False
    print(f"Polling {health_url}...")
    for attempt in range(1, max_retries + 1):
        try:
            res = httpx.get(health_url, timeout=5.0)
            if res.status_code == 200:
                print(f"  [OK] /health responded 200 in attempt {attempt}: {res.json()}")
                healthy = True
                break
        except Exception:
            time.sleep(retry_delay)

    if not healthy:
        print(f"  [FAIL] /health did not return 200 after {max_retries} attempts.")
        return False

    # 2. Check /ready
    ready_url = f"{base_url}/ready"
    print(f"Checking {ready_url}...")
    try:
        res = httpx.get(ready_url, timeout=5.0)
        if res.status_code != 200:
            print(f"  [FAIL] /ready returned status {res.status_code}: {res.text}")
            return False
        ready_data = res.json()
        print(f"  [OK] /ready returned 200: {ready_data}")
        if ready_data.get("status") != "ready":
            print("  [FAIL] /ready payload indicates model is not ready.")
            return False
    except Exception as e:
        print(f"  [FAIL] Exception querying /ready: {e}")
        return False

    # 3. Check /api/v1/model-info
    info_url = f"{base_url}/api/v1/model-info"
    print(f"Checking {info_url}...")
    try:
        res = httpx.get(info_url, timeout=5.0)
        if res.status_code != 200:
            print(f"  [FAIL] /api/v1/model-info returned status {res.status_code}: {res.text}")
            return False
        info_data = res.json()
        print(f"  [OK] /api/v1/model-info returned 200: {info_data.get('model_name')} v{info_data.get('model_version')}")
    except Exception as e:
        print(f"  [FAIL] Exception querying /api/v1/model-info: {e}")
        return False

    # 4. Check /api/v1/predict with sample payload
    predict_url = f"{base_url}/api/v1/predict"
    test_payload = {
        "text": "Laptop display flickering and screen goes completely black when moving lid.",
        "blocking_team": False,
    }
    print(f"Testing inference at {predict_url}...")
    try:
        res = httpx.post(predict_url, json=test_payload, timeout=5.0)
        if res.status_code != 200:
            print(f"  [FAIL] /api/v1/predict returned status {res.status_code}: {res.text}")
            return False
        pred = res.json()
        print(
            f"  [OK] /api/v1/predict successful: Category='{pred.get('category')}', "
            f"Decision='{pred.get('decision')}', Confidence={pred.get('category_confidence')}"
        )
        assert pred.get("category") == "Hardware"
        assert pred.get("decision") in ("auto_route", "human_review")
    except Exception as e:
        print(f"  [FAIL] Exception querying /api/v1/predict: {e}")
        return False

    print("\nALL SMOKE TESTS PASSED SUCCESSFULLY!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Container / Deployment Smoke Tester")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Root URL of application")
    parser.add_argument("--retries", type=int, default=30, help="Max retry attempts for initial health check")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between retries in seconds")
    args = parser.parse_args()

    success = run_smoke_test(base_url=args.base_url, max_retries=args.retries, retry_delay=args.delay)
    if not success:
        sys.exit(1)
    sys.exit(0)
