import os, time, requests, pytest

pytestmark = pytest.mark.integration

BASE = os.getenv("SERVER_BASE", "http://localhost:8010")

def wait(url, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(url, timeout=2)
            if r.ok:
                return r
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"Timeout waiting for {url}")

def test_health():
    r = wait(f"{BASE}/health")
    data = r.json()
    assert data.get("status") == "ok"
