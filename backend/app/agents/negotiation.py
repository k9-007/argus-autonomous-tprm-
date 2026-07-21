"""Negotiation Agent.

Turns missing/gated evidence into concrete, human-authorized actions:
trust-center access requests, NDA-signing tasks routed to an Approver, and
drafted vendor doc-request emails. Argus never auto-signs legal terms.
"""

from __future__ import annotations

from ..config import settings
from .base import Emit

NAME = "Negotiation Agent"


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    tasks = ctx.setdefault("tasks", [])
    emit(NAME, "Resolving evidence gaps: access requests, NDAs and vendor outreach...", "working")

    # Access actions from trust-center ingestion.
    for action in ctx.get("access_actions", []):
        if action["action"] == "sign_nda":
            tasks.append({
                "title": f"Sign NDA to unlock {action['doc_name']}",
                "task_type": "nda",
                "owner": "Approver",
                "status": "open",
                "detail": f"{action['note']} Platform: {action['platform']}.",
            })
        else:
            tasks.append({
                "title": f"Request access to {action['doc_name']}",
                "task_type": "access_request",
                "owner": "Argus (auto-submitted)",
                "status": "in_progress",
                "detail": action["note"],
            })

    # Missing baseline docs with no trust center -> draft vendor email.
    have_types = {d.get("doc_type") for d in ctx.get("documents", [])}
    if "soc2_type2" not in have_types and "iso27001" not in have_types:
        draft = (
            f"Subject: Security documentation request - {vendor['name']}\n\n"
            f"Hi {vendor['name']} team,\n\n"
            "As part of our vendor security review, could you share your latest SOC 2 Type II "
            "or ISO 27001 report, DPA, and subprocessor list? We can sign an NDA if required.\n\n"
            "Thank you,\nSecurity Team (via Argus)"
        )
        tasks.append({
            "title": "Email vendor for SOC 2 / ISO 27001 + DPA",
            "task_type": "access_request",
            "owner": "Argus (drafted)",
            "status": "open",
            "detail": draft,
        })

    # Vendor-collaboration invite (the network moat) if no trust center at all.
    if not vendor.get("trust_center_url"):
        invite = f"{settings.PUBLIC_URL}/passport/claim/{ctx.get('vendor_key','')}"
        tasks.append({
            "title": "Invite vendor to claim Trust Passport",
            "task_type": "access_request",
            "owner": "Argus (drafted)",
            "status": "open",
            "detail": f"Invite the vendor to upload evidence once at {invite}; reused across all future reviews.",
        })

    emit(NAME, f"Created {len(tasks)} outreach/access tasks (NDAs routed to Approver).", "done")
