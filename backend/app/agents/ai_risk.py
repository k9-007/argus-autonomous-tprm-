"""AI-Vendor Risk Agent (Argus differentiator).

Assesses the AI-specific risk dimension no traditional TPRM tool treats as
first-class: prompt injection, tool/action permissions, data retention &
training use, and autonomous actions - mapping toward ISO 42001.
"""

from __future__ import annotations

from ..llm import complete_json, llm_available
from .base import Emit

NAME = "AI-Vendor Risk Agent"

_HIGH_RISK_KEYS = {
    "prompt_injection_exposure": {"high": "high", "critical": "critical"},
}


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    if vendor.get("vendor_type") not in ("ai_agent", "mcp") and not ctx.get("ai_profile"):
        emit(NAME, "Vendor is not an AI/agent/MCP provider - AI-specific risk not applicable.", "info")
        ctx["ai_risk"] = {"applicable": False}
        return

    emit(NAME, "Evaluating prompt injection, tool permissions, data retention and autonomous actions...", "working")

    profile = ctx.get("ai_profile")
    if not profile and llm_available():
        profile = complete_json(
            system="You are an AI governance analyst assessing an AI vendor under ISO 42001.",
            user=(
                f"Assess AI risk for {vendor['name']} ({vendor.get('description','')}). "
                "Return JSON: sends_data_to_models, model_providers (list), data_retention, "
                "training_use, tool_permissions, autonomous_actions, prompt_injection_exposure "
                "(low|medium|high|critical)."
            ),
            fallback={},
        )
    profile = profile or {
        "prompt_injection_exposure": "high",
        "data_retention": "Undisclosed",
        "training_use": "Undisclosed",
        "tool_permissions": "Undisclosed",
        "autonomous_actions": "Undisclosed",
    }
    ctx["ai_profile"] = profile

    # Convert profile into concrete findings.
    exposure = str(profile.get("prompt_injection_exposure", "medium")).lower()
    if exposure in ("high", "critical"):
        ctx.setdefault("findings", []).append({
            "category": "ai_risk", "severity": exposure,
            "title": "Elevated prompt-injection exposure",
            "detail": "Vendor ingests untrusted content into model context; injection could trigger unintended tool actions.",
            "sources": [],
        })
    retention = str(profile.get("data_retention", "")).lower()
    if "undisclosed" in retention or ("retain" in retention and "zero" not in retention):
        ctx.setdefault("findings", []).append({
            "category": "ai_risk", "severity": "high",
            "title": "Data retention / training use not zero by default",
            "detail": f"Retention posture: {profile.get('data_retention','undisclosed')}. "
                      f"Training use: {profile.get('training_use','undisclosed')}.",
            "sources": [],
        })
    tools = str(profile.get("tool_permissions", "")).lower()
    if "full" in tools or "static token" in tools or "undisclosed" in tools:
        ctx.setdefault("findings", []).append({
            "category": "ai_risk", "severity": "high",
            "title": "Broad or unscoped tool permissions",
            "detail": f"Tool permissions: {profile.get('tool_permissions','undisclosed')}.",
            "sources": [],
        })

    ctx["ai_risk"] = {"applicable": True, "profile": profile}
    emit(NAME, f"AI risk profiled: injection={exposure}, "
               f"retention='{profile.get('data_retention','undisclosed')}'. Findings raised.", "done")
