"""Inherent + residual risk scoring with driver-level explanations.

Scores are 0-100 (higher = more risk). Inherent risk reflects the vendor's base
exposure (data sensitivity, system access, vendor type). Residual risk applies
the mitigating effect of verified controls and the aggravating effect of
findings and live monitoring events. Every score ships with an explainable
driver breakdown, which is what auditors and boards require.
"""

from __future__ import annotations

_SENSITIVITY_WEIGHT = {
    "none": 5, "low": 20, "medium": 40, "high": 65, "regulated": 85, "unknown": 45,
}
_ACCESS_WEIGHT = {
    "none": 0, "limited": 15, "production": 30, "unknown": 15,
}
_TYPE_WEIGHT = {
    "saas": 0, "ai_agent": 12, "mcp": 18,
}
_SEVERITY_POINTS = {"low": 3, "medium": 8, "high": 16, "critical": 28}


def _band(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def compute_inherent(vendor: dict) -> tuple[float, list[dict]]:
    drivers = []
    s = _SENSITIVITY_WEIGHT.get(vendor.get("data_sensitivity", "unknown"), 45)
    drivers.append({"factor": "Data sensitivity", "impact": +s,
                    "detail": f"Handles {vendor.get('data_sensitivity','unknown')} data."})
    a = _ACCESS_WEIGHT.get(vendor.get("system_access", "unknown"), 15)
    drivers.append({"factor": "System access", "impact": +a,
                    "detail": f"{vendor.get('system_access','unknown')} access to systems."})
    t = _TYPE_WEIGHT.get(vendor.get("vendor_type", "saas"), 0)
    if t:
        drivers.append({"factor": "AI/agent exposure", "impact": +t,
                        "detail": f"Vendor type '{vendor.get('vendor_type')}' introduces AI-specific risk."})
    inherent = min(100.0, float(s + a + t))
    return round(inherent, 1), drivers


def tier_from_inherent(inherent: float, vendor: dict) -> int:
    """Map to a 1-4 tier (1 = critical). Regulated data or production access -> Tier 1."""
    if vendor.get("data_sensitivity") == "regulated" or vendor.get("system_access") == "production":
        return 1
    if inherent >= 60:
        return 1
    if inherent >= 45:
        return 2
    if inherent >= 25:
        return 3
    return 4


def compute_residual(
    inherent: float,
    coverage_pct: float,
    questionnaire_pct: float,
    findings: list[dict],
    monitoring: list[dict],
) -> tuple[float, str, list[dict]]:
    drivers: list[dict] = []
    residual = inherent

    # Controls mitigate inherent risk (up to ~60% reduction at full coverage).
    mitigation = (coverage_pct / 100.0) * inherent * 0.6
    if mitigation:
        drivers.append({"factor": "Verified controls", "impact": -round(mitigation, 1),
                        "detail": f"{coverage_pct}% framework control coverage reduces exposure."})
    residual -= mitigation

    # Questionnaire completeness gives a smaller assurance credit.
    q_credit = (questionnaire_pct / 100.0) * 8
    if q_credit:
        drivers.append({"factor": "Questionnaire assurance", "impact": -round(q_credit, 1),
                        "detail": f"{questionnaire_pct}% of questions evidence-backed."})
    residual -= q_credit

    # Findings add risk back.
    for f in findings:
        pts = _SEVERITY_POINTS.get(f.get("severity", "medium"), 8)
        residual += pts
        drivers.append({"factor": f"Finding: {f.get('title','')[:60]}", "impact": +pts,
                        "detail": f.get("detail", "")[:160] or f.get("category", "")})

    # Active monitoring events add risk.
    for m in monitoring:
        pts = _SEVERITY_POINTS.get(m.get("severity", "medium"), 8) * 0.6
        if m.get("severity") in ("high", "critical"):
            residual += pts
            drivers.append({"factor": f"Live signal: {m.get('title','')[:60]}", "impact": +round(pts, 1),
                            "detail": m.get("detail", "")[:160]})

    residual = max(0.0, min(100.0, residual))
    return round(residual, 1), _band(residual), drivers


def decision_from_residual(residual: float, tier: int) -> str:
    """Map residual score + tier to a decision recommendation."""
    if residual >= 75:
        return "block"
    if residual >= 50:
        return "approve_with_conditions"
    if tier == 1 and residual >= 40:
        return "approve_with_conditions"
    return "approve"
