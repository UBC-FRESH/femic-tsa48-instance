"""Make the framework scripts in ``scripts/`` importable from the test suite."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS: Path = Path(__file__).resolve().parents[1] / "scripts"
ROOT: Path = Path(__file__).resolve().parents[1]
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
