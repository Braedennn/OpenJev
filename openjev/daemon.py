"""OpenJev Jev daemon: local HTTP bridge to TypeSafe's Jev, with a trace log.

The daemon reuses the jev-studio core so every question is built in the exact
shape Jev expects (`noul`, `choice`, `score` with the core's criteria builders).
Every call is appended to the trace JSONL, which is the proof that Jev was
consulted for a given step.
"""
from __future__ import annotations

import contextlib
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from jev_studio.cli.core import run_ask
from jev_studio.cli.errors import CliError
from jev_studio.cli.utils import choice

from .env import load_dsh_credentials, load_env
from .jev import JevClient

DEFAULT_PORT = 8931


class JevProvider:
    """Resolve the Jev client per request so a key saved in the UI applies live."""

    def __init__(self, client: JevClient | None = None):
        self._fixed = client
        self._client: JevClient | None = None
        self._key: str | None = None

    def client(self) -> JevClient:
        if self._fixed is not None:
            return self._fixed
        load_env()
        stored = load_dsh_credentials()
        if stored:
            os.environ["TYPESAFE_API_KEY"] = stored
        key = os.environ.get("TYPESAFE_API_KEY")
        if self._client is None or key != self._key:
            self._key = key
            self._client = JevClient()
        return self._client


def trace_path() -> Path:
    override = os.environ.get("OPENJEV_TRACE")
    if override:
        return Path(override)
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    return home / ".openjev" / "trace.jsonl"


_trace_lock = threading.Lock()


def record(entry: dict[str, Any]) -> dict[str, Any]:
    entry.setdefault("ts", time.time())
    path = trace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _trace_lock, path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def _digest(value: Any, limit: int = 400) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit]


def skill_route(client: JevClient, task: str, skills: dict[str, str]) -> dict[str, Any]:
    if not isinstance(task, str) or not task.strip():
        raise CliError("task must be a non-empty string")
    if not isinstance(skills, dict) or len(skills) < 2:
        raise CliError("skills must map at least two skill names to descriptions")
    criteria = dict(skills)
    criteria["none"] = "No listed skill matches this task"
    questions = {
        "skill": choice("Which skill best matches this task?", criteria),
    }
    out = run_ask(client._ask, task, questions)  # noqa: SLF001 - same package
    answer = out["answers"].get("skill", {})
    probabilities = {k: float(v) for k, v in (answer.get("probabilities") or {}).items()}
    ranking = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    return {
        "command": "skill_route",
        "model": out["model"],
        "provider": out["provider"],
        "skill": answer.get("choice"),
        "confidence": answer.get("confidence"),
        "probabilities": probabilities,
        "ranking": [{"skill": name, "probability": p} for name, p in ranking],
        "usage": out["usage"],
    }


def dispatch(client: JevClient, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """Run one daemon request. Raises CliError on bad input."""
    if not isinstance(body, dict):
        raise CliError("request body must be a JSON object")
    if endpoint == "/ask":
        if "state" not in body or "questions" not in body:
            raise CliError("/ask requires state and questions")
        return client.ask(body["state"], body["questions"])
    if endpoint == "/verify":
        return client.verify(body.get("claims"), body.get("evidence"), body.get("auto_accept"))
    if endpoint == "/screen":
        return client.screen(
            body.get("text", ""),
            body.get("purpose"),
            body.get("block_at"),
            body.get("review_at"),
        )
    if endpoint == "/classify":
        return client.classify(
            body.get("text", ""),
            body.get("labels"),
            bool(body.get("multi", False)),
            body.get("instructions"),
            min_confidence=body.get("min_confidence"),
            threshold=body.get("threshold"),
        )
    if endpoint == "/route":
        return client.route(
            body.get("request", ""),
            body.get("handlers"),
            body.get("instructions"),
            body.get("min_confidence"),
        )
    if endpoint == "/skill_route":
        return skill_route(client, body.get("task", ""), body.get("skills") or {})
    raise CliError(f"unknown endpoint {endpoint}")


def _status(client: JevClient) -> dict[str, Any]:
    from jev_studio.cli.credentials import ENV_VAR, resolve_credentials, with_stored_credentials
    from jev_studio.cli.provider import resolve_provider

    raw = dict(os.environ)
    rows = resolve_credentials(raw)
    return {
        "model": client.model,
        "provider": resolve_provider(with_stored_credentials(raw), "auto"),
        "trace": str(trace_path()),
        "credentials": [
            {"provider": r["provider"], "env_var": ENV_VAR[r["provider"]], "source": r["source"]} for r in rows
        ],
    }


def _read_trace(limit: int) -> dict[str, Any]:
    path = trace_path()
    if not path.exists():
        return {"trace": str(path), "entries": []}
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines[-max(0, limit):]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"trace": str(path), "entries": entries}


def make_handler(provider: JevProvider) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "openjev-daemon/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            if os.environ.get("OPENJEV_DEBUG") == "1":
                super().log_message(fmt, *args)

        def _send(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            try:
                if path == "/health":
                    self._send(200, {"ok": True, "service": "openjev-daemon"})
                elif path == "/status":
                    self._send(200, _status(provider.client()))
                elif path == "/trace":
                    limit = 50
                    if "limit=" in self.path:
                        try:
                            limit = int(self.path.split("limit=", 1)[1].split("&", 1)[0])
                        except ValueError:
                            limit = 50
                    self._send(200, _read_trace(limit))
                else:
                    self._send(404, {"error": f"unknown path {path}"})
            except CliError as err:
                self._send(400, {"error": str(err)})

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._send(400, {"error": "request body is not valid JSON"})
                return
            source = str(body.get("source") or "http")
            started = time.time()
            try:
                result = dispatch(provider.client(), path, body)
            except CliError as err:
                record({"source": source, "endpoint": path, "error": str(err), "latency_ms": 0})
                self._send(400, {"error": str(err)})
                return
            except Exception as err:  # transport or malformed API response
                record({"source": source, "endpoint": path, "error": str(err), "latency_ms": 0})
                self._send(502, {"error": f"jev call failed: {err}"})
                return
            latency_ms = round((time.time() - started) * 1000)
            record(
                {
                    "source": source,
                    "endpoint": path,
                    "latency_ms": latency_ms,
                    "model": result.get("model"),
                    "provider": result.get("provider"),
                    "usage": result.get("usage"),
                    "input": _digest({k: v for k, v in body.items() if k not in ("questions",)}),
                    "answers": result.get("answers") or result.get("results") or result.get("recommendation")
                    or {k: result[k] for k in ("label", "confidence", "handler", "skill") if k in result},
                }
            )
            self._send(200, result)

    return Handler


def make_server(port: int = DEFAULT_PORT, client: JevClient | None = None) -> ThreadingHTTPServer:
    provider = client if isinstance(client, JevProvider) else JevProvider(client)
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(provider))


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="openjev-daemon", description="Local Jev bridge for OpenJev.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("OPENJEV_DAEMON_PORT", DEFAULT_PORT)))
    args = parser.parse_args(argv)
    loaded = load_env()
    server = make_server(args.port)
    print(f"openjev-daemon: http://127.0.0.1:{args.port}  trace={trace_path()}  env={loaded or 'none'}", flush=True)
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()


if __name__ == "__main__":
    main()
