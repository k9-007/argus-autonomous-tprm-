"""Security Questionnaire Agent.

Auto-completes standard questionnaires (SIG Lite + CAIQ v4, plus an AI addendum
for AI/agent/MCP vendors), citing source evidence per answer and flagging
unbacked self-attestation as low confidence.
"""

from __future__ import annotations

from ..compliance.questionnaires import answer_questionnaire
from .base import Emit

NAME = "Questionnaire Agent"


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    documents = ctx.get("documents", [])
    include_ai = vendor.get("vendor_type") in ("ai_agent", "mcp")

    emit(NAME, "Auto-completing SIG Lite and CAIQ v4 with cited evidence...", "working")

    results = []
    total_q = 0
    total_answered = 0
    for fw in ("SIG Lite", "CAIQ v4"):
        r = answer_questionnaire(fw, documents, include_ai=include_ai)
        results.append(r)
        total_q += r["total"]
        total_answered += r["answered"]

    ctx["questionnaires"] = results
    ctx["questionnaire_pct"] = round(100 * total_answered / (total_q or 1), 1)

    emit(NAME, f"Completed {total_q} questions; {total_answered} evidence-backed "
               f"({ctx['questionnaire_pct']}%). Remaining flagged as unverified.", "done")
