import os
import requests
import pytest
pytestmark = pytest.mark.integration

BASE = os.getenv("SERVER_BASE", "http://localhost:8010")

def test_metrics_exposed():
    r = requests.get(f"{BASE}/metrics", timeout=5)
    assert r.ok
    print(r.content)
    assert b"python_info" in r.content
