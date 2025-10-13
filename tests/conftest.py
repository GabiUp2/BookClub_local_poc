# Test configuration to ensure `src/` layout is importable.
# Uses British English in comments.

import os
import sys
from pathlib import Path

# Add project `src/` to sys.path for tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
