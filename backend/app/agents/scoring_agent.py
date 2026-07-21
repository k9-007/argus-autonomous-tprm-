"""Risk Scoring Agent.

Combines inherent risk, verified control coverage, questionnaire assurance,
findings and live monitoring signals into an explainable residual score with a
driver-level breakdown and a decision recommendation.
"""

from __future__ import annotations

from ..scoring import compute_residual, decision_from_residual
from .base import Emit

NAME = "Risk Scoring Agent"


def run(ctx: dict, emit: Emit) -> None:
    emit(NAME, "Calculating residual risk and explaining the drivers...", "working")

    inherent = ctx.get("inherent", 50.0)
    coverage_pct = ctx.get("coverage_summary", {}).get("coverage_pct", 0.0)
    questionnaire_pct = ctx.get("questionnaire_pct", 0.0)
    findings = ctx.get("findings", [])
    monitoring = ctx.get("monitoring", [])

    residual, band, residual_drivers = compute_residual(
        inherent, coverage_pct, questionnaire_pct, findings, monitoring
    )

    drivers = [{"factor": "Inherent exposure", "impact": inherent,
                "detail": "Baseline risk from data sensitivity, access and vendor type."}]
    drivers += ctx.get("inherent_drivers", [])
    drivers += residual_drivers

    tier = ctx["vendor"].get("inherent_tier", 3)
    decision = decision_from_residual(residual, tier)

    ctx["inherent_score"] = inherent
    ctx["residual_score"] = residual
    ctx["risk_band"] = band
    ctx["risk_drivers"] = drivers
    ctx["decision"] = decision

    emit(NAME, f"Residual risk {residual}/100 ({band}). Recommendation: {decision.replace('_',' ')}.", "done")
