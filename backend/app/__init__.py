"""Kollamo.ai Backend Application Package."""

import sys
from pathlib import Path

# Ensure root repository directory is in sys.path so 'backend.app' and 'ml' imports always resolve
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
