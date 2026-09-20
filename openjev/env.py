"""Load the OpenJev .env file without overriding the ambient environment."""
from __future__ import annotations

import os
from pathlib import Path


def default_env_path() -> Path:
    override = os.environ.get("OPENJEV_ENV")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / ".env"


def load_env(path: Path | str | None = None) -> Path | None:
    target = Path(path) if path is not None else default_env_path()
    if not target.exists():
        return None
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)
    return target
