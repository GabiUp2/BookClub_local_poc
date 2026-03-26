import subprocess
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.expected_duration("long")
def test_app_can_reach_server(docker_prefix):
    cmd = docker_prefix + [
        "docker",
        "compose",
        "exec",
        "-T",
        "bookclub-app",
        "wget",
        "-qO-",
        "http://bookclub-preprocessing-server:8010/health",
    ]
    out = subprocess.check_output(cmd, text=True)
    assert '"status":"ok"' in out
