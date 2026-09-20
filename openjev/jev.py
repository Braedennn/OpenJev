"""Typed Jev decisions for any AI host.

Wraps the jev-studio CLI core (transport, prompts, validation) so MCP hosts
and harnesses can call Jev directly: ask, verify, screen, classify, route.
"""
from __future__ import annotations

import os
from typing import Any

from jev_studio.cli.context import build_context
from jev_studio.cli.core import (
    parse_label_json,
    parse_questions,
    run_ask,
    run_classify,
    run_classify_multi,
    run_route,
    run_screen,
    run_verify,
)
from jev_studio.cli.errors import CliError
from jev_studio.cli.provider import AskFn


def evidence_items(raw: Any) -> list[dict]:
    if not isinstance(raw, list) or not raw:
        raise CliError("evidence must be a non-empty list of strings or {id?, text} objects.")
    out: list[dict] = []
    for i, item in enumerate(raw):
        if isinstance(item, str) and item.strip():
            out.append({"id": f"e{i + 1}", "text": item})
        elif isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
            out.append({"id": str(item.get("id") or f"e{i + 1}"), "text": item["text"]})
        else:
            raise CliError(f"evidence[{i}] must be a non-empty string or an object with a non-empty text field.")
    return out


def handler_specs(raw: Any) -> dict:
    if not isinstance(raw, dict) or not raw:
        raise CliError("handlers must be a non-empty object mapping names to descriptions or specs.")
    out: dict[str, dict] = {}
    for name, spec in raw.items():
        if spec is None or isinstance(spec, str):
            out[name] = {"description": spec}
        elif isinstance(spec, dict):
            out[name] = spec
        else:
            raise CliError(f'handler "{name}" must be a description string or an object.')
    return out


class JevClient:
    """Jev decisions bound to stored credentials and the user's config."""

    def __init__(self, ask: AskFn | None = None, env: dict[str, str] | None = None):
        ctx = build_context({}, env=env if env is not None else dict(os.environ))
        self.config = ctx.config
        self._ask = ask if ask is not None else ctx.ask()

    @property
    def model(self) -> str:
        return str(self.config.get("model", "jev-latest"))

    @property
    def provider(self) -> str:
        return str(self.config.get("provider", "auto"))

    def ask(self, state: Any, questions: dict) -> dict:
        return run_ask(self._ask, state, parse_questions(questions))

    def verify(self, claims: list[str], evidence: Any, auto_accept: float | None = None) -> dict:
        if not isinstance(claims, list) or not claims or not all(isinstance(c, str) and c.strip() for c in claims):
            raise CliError("claims must be a non-empty list of strings.")
        threshold = float(auto_accept if auto_accept is not None else self.config["verify"]["autoAccept"])
        return run_verify(self._ask, claims, evidence_items(evidence), threshold)

    def screen(
        self,
        text: str,
        purpose: str | None = None,
        block_at: float | None = None,
        review_at: float | None = None,
    ) -> dict:
        cfg = self.config["screen"]
        b = float(block_at if block_at is not None else cfg["blockAt"])
        r = float(review_at if review_at is not None else cfg["reviewAt"])
        return run_screen(self._ask, text, purpose, b, r)

    def classify(
        self,
        text: Any,
        labels: Any,
        multi: bool = False,
        instructions: str | None = None,
        other: bool = False,
        min_confidence: float | None = None,
        threshold: float | None = None,
    ) -> dict:
        parsed = parse_label_json(labels)
        if multi:
            t = float(threshold if threshold is not None else self.config["classify"]["threshold"])
            return run_classify_multi(self._ask, text, parsed, instructions, t)
        mc = float(min_confidence if min_confidence is not None else self.config["classify"]["minConfidence"])
        return run_classify(self._ask, text, parsed, instructions, other, mc)

    def route(
        self,
        request: Any,
        handlers: Any,
        instructions: str | None = None,
        min_confidence: float | None = None,
    ) -> dict:
        mc = float(min_confidence if min_confidence is not None else self.config["route"]["minConfidence"])
        return run_route(self._ask, request, handler_specs(handlers), instructions, mc)
