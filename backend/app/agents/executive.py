"""Executive Agent.

Produces the board-ready decision narrative: what the vendor is, the residual
risk, the top drivers, the compliance posture, and the recommended decision with
conditions. Uses GPT-5.6 when available, otherwise a deterministic template.
"""

from __future__ import annotations

from ..llm import complete_json, llm_available
from .base import Emit

NAME = "Executive Agent"

_DECISION_LABEL = {
    "approve": "APPROVE",
    "approve_with_conditions": "APPROVE WITH CONDITIONS",
    "block": "BLOCK",
    "pending": "PENDING",
}


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    emit(NAME, "Generating board-ready risk decision report...", "working")

    residual = ctx.get("residual_score", 0)
    band = ctx.get("risk_band", "medium")
    decision = ctx.get("decision", "pending")
    coverage = ctx.get("coverage_summary", {})
    findings = ctx.get("findings", [])
    top_findings = sorted(
        findings, key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.get("severity"), 3)
    )[:3]

    conditions = []
    if decision != "approve":
        for f in top_findings:
            if f.get("severity") in ("high", "critical"):
                conditions.append(f"Remediate: {f.get('title')}")
    if not conditions and decision == "approve_with_conditions":
        conditions.append("Obtain and review gated audit evidence before go-live.")

    summary = None
    if llm_available():
        out = complete_json(
            system="You are a CISO writing a concise board-ready third-party risk summary.",
            user=(
                f"Vendor: {vendor['name']} ({vendor.get('category')}). "
                f"Residual risk: {residual}/100 ({band}). Decision: {decision}. "
                f"Control coverage: {coverage.get('coverage_pct')}%. "
                f"Top findings: {[f.get('title') for f in top_findings]}. "
                "Return JSON with a single key 'summary' containing a 3-4 sentence executive summary."
            ),
            fallback={},
        )
        summary = out.get("summary")

    if not summary:
        finding_str = "; ".join(f.get("title") for f in top_findings) or "no material findings"
        summary = (
            f"{vendor['name']} ({vendor.get('category','vendor')}) presents {band} residual risk "
            f"({residual}/100) at Tier {vendor.get('inherent_tier')}. Verified control coverage is "
            f"{coverage.get('coverage_pct', 0)}% across required frameworks. Key drivers: {finding_str}. "
            f"Recommendation: {_DECISION_LABEL.get(decision)}."
            + (f" Conditions: {'; '.join(conditions)}." if conditions else "")
        )

    ctx["summary"] = summary
    ctx["conditions"] = conditions
    emit(NAME, f"Decision: {_DECISION_LABEL.get(decision)} (residual {residual}/100). Report ready.", "done")
