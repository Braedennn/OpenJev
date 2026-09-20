"""OpenJev MCP server: real Jev decisions over stdio.

Exposes Jev as callable tools so any MCP host (Codex, opencode, Claude
Desktop) can route, verify, screen, classify, and ask typed questions.
"""
from __future__ import annotations

import os
from typing import Any

from jev_studio.cli.credentials import ENV_VAR, resolve_credentials, with_stored_credentials
from jev_studio.cli.errors import CliError
from jev_studio.cli.provider import resolve_provider

try:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

from .env import load_env
from .jev import JevClient

mcp = MCPServer("openjev")

_client: JevClient | None = None


def _client_or_create() -> JevClient:
    global _client
    if _client is None:
        _client = JevClient()
    return _client


def _guard(action: Any, **kwargs: Any) -> dict:
    try:
        return action(**kwargs)
    except CliError as err:
        return {"error": str(err)}


@mcp.tool(
    name="jev_ask",
    description=(
        "Ask Jev typed questions about any state and get typed answers with probabilities. "
        "questions maps ids to objects: {type: 'noul'|'choice'|'score', instructions: str, "
        "criteria: {label: description} for choice, or criteria: [level, ...] for score}."
    ),
)
def jev_ask(state: Any, questions: dict) -> dict:
    return _guard(_client_or_create().ask, state=state, questions=questions)


@mcp.tool(
    name="jev_verify",
    description=(
        "Check claims against evidence. Returns per-claim verdicts "
        "(verified/contradicted/unsupported), probabilities, and the supporting evidence id. "
        "Use before repeating any factual claim; prefer a claim that is not verified be dropped or hedged."
    ),
)
def jev_verify(claims: list[str], evidence: list[Any], auto_accept: float | None = None) -> dict:
    return _guard(_client_or_create().verify, claims=claims, evidence=evidence, auto_accept=auto_accept)


@mcp.tool(
    name="jev_screen",
    description=(
        "Screen untrusted text before it enters the model context. Flags prompt injection, "
        "empty/boilerplate content, and irrelevance to a purpose. Recommends pass/review/block/skip."
    ),
)
def jev_screen(
    text: str,
    purpose: str | None = None,
    block_at: float | None = None,
    review_at: float | None = None,
) -> dict:
    return _guard(
        _client_or_create().screen,
        text=text,
        purpose=purpose,
        block_at=block_at,
        review_at=review_at,
    )


@mcp.tool(
    name="jev_classify",
    description=(
        "Classify text into labels. labels is a list of strings or {label, description} objects, "
        "or a {label: description} object. multi=true asks each label independently (probability + applies)."
    ),
)
def jev_classify(
    text: str,
    labels: Any,
    multi: bool = False,
    instructions: str | None = None,
    min_confidence: float | None = None,
    threshold: float | None = None,
) -> dict:
    return _guard(
        _client_or_create().classify,
        text=text,
        labels=labels,
        multi=multi,
        instructions=instructions,
        min_confidence=min_confidence,
        threshold=threshold,
    )


@mcp.tool(
    name="jev_route",
    description=(
        "Pick a handler for a request and fill its closed-set arguments in one call. "
        "handlers is {name: description} or {name: {description, args}} where args is "
        "{arg: {type: 'noul'|'choice'|'score', options/levels/instructions}}."
    ),
)
def jev_route(
    request: Any,
    handlers: dict,
    instructions: str | None = None,
    min_confidence: float | None = None,
) -> dict:
    return _guard(
        _client_or_create().route,
        request=request,
        handlers=handlers,
        instructions=instructions,
        min_confidence=min_confidence,
    )


@mcp.tool(
    name="jev_status",
    description="Report the Jev model, provider, and credential source OpenJev is using (never the key itself).",
)
def jev_status() -> dict:
    try:
        raw_env = dict(os.environ)
        rows = resolve_credentials(raw_env)
        return {
            "model": _client_or_create().model,
            "provider": resolve_provider(with_stored_credentials(raw_env), "auto"),
            "credentials": [
                {"provider": r["provider"], "env_var": ENV_VAR[r["provider"]], "source": r["source"]} for r in rows
            ],
        }
    except CliError as err:
        return {"error": str(err)}


def main() -> None:
    load_env()
    mcp.run()


if __name__ == "__main__":
    main()
