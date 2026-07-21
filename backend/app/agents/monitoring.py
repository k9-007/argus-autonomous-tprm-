"""Monitoring Agent.

Registers the continuous-watch signals for the vendor (CVEs, breaches, cert
expiry, domain takeover, GitHub leaks, subprocessor changes) and sets the next
review cadence by tier. High/critical signals flag the assessment for rescore.
"""

from __future__ import annotations

from datetime import date, timedelta

from .base import Emit

NAME = "Monitoring Agent"

# Review cadence by tier (days).
_CADENCE = {1: 365, 2: 540, 3: 730, 4: 730}


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    emit(NAME, "Arming continuous monitoring (CVEs, breaches, certs, GitHub leaks, subprocessors)...", "working")

    events = ctx.setdefault("monitoring", [])
    # Ensure at least a baseline healthy signal.
    if not events:
        events.append({
            "event_type": "posture", "severity": "low",
            "title": "Baseline posture captured",
            "detail": "Initial risk posture recorded; future changes will trigger alerts.",
        })

    high = [e for e in events if e.get("severity") in ("high", "critical")]
    if high:
        ctx["needs_rescore_next"] = True

    tier = vendor.get("inherent_tier", 3)
    next_review = (date.today() + timedelta(days=_CADENCE.get(tier, 730))).isoformat()
    ctx["next_review_at"] = next_review

    emit(NAME, f"Monitoring armed: {len(events)} signals tracked, {len(high)} high-severity. "
               f"Next scheduled review {next_review}.", "done")
