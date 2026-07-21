"""Intake / Profile Agent.

Builds the vendor profile (what it does, data it touches, system access),
classifies SaaS vs AI-agent vs MCP, and sets the inherent-risk tier that drives
assessment depth.
"""

from __future__ import annotations

from ..data.fixtures import lookup_demo
from ..llm import complete_json, llm_available
from ..scoring import compute_inherent, tier_from_inherent
from .base import Emit

NAME = "Intake Agent"


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    emit(NAME, f"Reading request for {vendor['name']} and building risk profile...", "working")

    demo = lookup_demo(ctx.get("vendor_key", ""))
    if demo:
        vendor.setdefault("description", demo.get("description"))
        vendor["category"] = vendor.get("category") or demo.get("category")
        vendor["vendor_type"] = vendor.get("vendor_type") or demo.get("vendor_type", "saas")
        if vendor.get("data_sensitivity", "unknown") == "unknown":
            vendor["data_sensitivity"] = demo.get("data_sensitivity", "medium")
        if vendor.get("system_access", "unknown") == "unknown":
            vendor["system_access"] = demo.get("system_access", "limited")
        if demo.get("ai_profile"):
            ctx["ai_profile"] = demo["ai_profile"]
    elif llm_available():
        profile = complete_json(
            system="You are a TPRM intake analyst. Classify a vendor for risk assessment.",
            user=(
                f"Vendor: {vendor['name']}. Website: {vendor.get('website')}. "
                "Return JSON with keys: category, vendor_type (saas|ai_agent|mcp), "
                "data_sensitivity (none|low|medium|high|regulated), "
                "system_access (none|limited|production), description."
            ),
            fallback={},
        )
        for k in ("category", "vendor_type", "description"):
            if profile.get(k):
                vendor[k] = vendor.get(k) or profile[k]
        if vendor.get("data_sensitivity", "unknown") == "unknown":
            vendor["data_sensitivity"] = profile.get("data_sensitivity", "medium")
        if vendor.get("system_access", "unknown") == "unknown":
            vendor["system_access"] = profile.get("system_access", "limited")

    # Sensible defaults if still unknown.
    if vendor.get("data_sensitivity", "unknown") == "unknown":
        vendor["data_sensitivity"] = "medium"
    if vendor.get("system_access", "unknown") == "unknown":
        vendor["system_access"] = "limited"
    vendor["vendor_type"] = vendor.get("vendor_type") or "saas"

    inherent, drivers = compute_inherent(vendor)
    tier = tier_from_inherent(inherent, vendor)
    vendor["inherent_tier"] = tier
    ctx["inherent"] = inherent
    ctx["inherent_drivers"] = drivers

    emit(
        NAME,
        f"Classified as {vendor['vendor_type'].upper()} | data={vendor['data_sensitivity']}, "
        f"access={vendor['system_access']} -> inherent risk {inherent}, Tier {tier}.",
        "done",
    )
