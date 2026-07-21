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

    tier = int(vendor.get("inherent_tier") or 3)
    questionnaire_names = ("SIG Core", "CAIQ v4") if tier == 1 else ("SIG Lite", "CAIQ v4") if tier == 2 else ("SIG Lite",)
    emit(NAME, f"Auto-completing {', '.join(questionnaire_names)} with cited evidence...", "working")

    results = []
    total_q = 0
    total_answered = 0
    for fw in questionnaire_names:
        r = answer_questionnaire(fw, documents, include_ai=include_ai)
        results.append(r)
        total_q += r["total"]
        total_answered += r["answered"]

    ctx["questionnaires"] = results
    ctx["questionnaire_pct"] = round(100 * total_answered / (total_q or 1), 1)

    emit(NAME, f"Completed {total_q} questions; {total_answered} evidence-backed "
               f"({ctx['questionnaire_pct']}%). Remaining flagged as unverified.", "done")
