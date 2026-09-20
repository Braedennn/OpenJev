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


def credentials_path(env: dict[str, str] | None = None) -> Path:
    env = env if env is not None else os.environ
    home = env.get("DSH_HOME") or str(Path.home() / ".dsh")
    return Path(home) / ".credentials.yaml"


def load_dsh_credentials(path: Path | str | None = None) -> str | None:
    """Read the Jev key the desktop UI stored under the `openjev` reference.

    The credential document is `refs:` (reference -> literal) and `records:`
    (provider -> fields). The Models page's Jev card writes a ref, so only the
    `refs:` section is parsed here.
    """
    target = Path(path) if path is not None else credentials_path()
    if not target.exists():
        return None
    inside = False
    for raw in target.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            inside = raw.strip() == "refs:"
            continue
        if not inside:
            continue
        key, sep, value = raw.strip().partition(":")
        if not sep:
            continue
        if key.strip().lower() in {"openjev", "jev", "typesafe", "typesafe_api_key"}:
            literal = value.strip().strip('"').strip("'")
            if literal:
                return literal
    return None
