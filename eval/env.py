"""Minimal, non-executing loader for repo-local credentials."""
from __future__ import annotations

import os
import stat
from pathlib import Path


def load_local_value(path: Path, key: str) -> bool:
    """Load one key from a mode-600 env file without sourcing shell syntax.

    An already-exported value wins. Other keys are ignored, and no interpolation
    or command execution is performed.
    """
    if os.environ.get(key):
        return False

    path = Path(path)
    if not path.exists():
        return False
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise PermissionError(f"{path} must not be readable by group or others; run chmod 600")

    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"{path}:{line_number}: expected NAME=value")
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not value:
            return False
        os.environ[key] = value
        return True
    return False
