# Test configuration to ensure `src/` layout is importable.
# Uses British English in comments.

import sys
import subprocess
from pathlib import Path

import pytest

# Add project `src/` to sys.path for tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(scope="session")
def docker_prefix() -> list[str]:
    """Determine how to invoke Docker.

    - Prefer direct `docker` if accessible.
    - Fallback to passwordless sudo (`sudo -n docker`) if configured.
    - Skip integration tests if neither works without prompting for a password.
    """
    def can_run(cmd: list[str]) -> bool:
        return (
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            == 0
        )

    if can_run(["docker", "compose", "ps"]):
        return []

    if can_run(["sudo", "-n", "docker", "compose", "ps"]):
        return ["sudo", "-n"]

    pytest.skip(
        "Docker daemon not accessible without sudo and passwordless sudo not configured. "
        "Skip integration tests or configure user in the docker group / NOPASSWD sudo."
    )
