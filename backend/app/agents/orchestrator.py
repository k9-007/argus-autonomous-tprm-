"""Crew orchestrator.

Plans and runs the agent crew for an assessment, streaming each step to the
activity feed (persisted so the SSE endpoint can replay it), then writes the
structured results back to the database and enriches the global Trust Passport.

Runs in a background thread, so it manages its own DB session.
"""

from __future__ import annotations

from datetime import datetime, UTC

from ..db import SessionLocal
from ..models import (
    Assessment, Vendor, Org, Document, Finding, ControlResult,
    Questionnaire, RiskScore, MonitoringEvent, Task, ActivityLog, TrustPassport,
    VendorStatus, VendorType, Decision, DocState,
)
from . import (
    intake, discovery_agent, compliance, questionnaire,
    ai_risk, scoring_agent, negotiation, monitoring, executive,
)

CREW = [
    intake, discovery_agent, compliance, questionnaire,
    ai_risk, scoring_agent, negotiation, monitoring, executive,
]


def _access_actions_from_documents(documents: list[dict]) -> list[dict]:
    actions = []
    for d in documents:
        if d.get("state") in ("requested", "nda_pending"):
            action = "sign_nda" if d.get("state") == "nda_pending" else "request_access"
            actions.append({
                "doc_type": d.get("doc_type"),
                "doc_name": d.get("name"),
                "action": action,
                "platform": d.get("source", "trust_center"),
                "note": (
                    "NDA must be signed by an authorized Approver before download."
                    if action == "sign_nda"
                    else "Access request submitted; awaiting vendor approval."
                ),
            })
    return actions


def run_assessment(assessment_id: str) -> None:
    db = SessionLocal()
    seq = {"n": 0}

    def emit(agent: str, message: str, status: str = "info") -> None:
        seq["n"] += 1
        db.add(ActivityLog(
            assessment_id=assessment_id, agent=agent, message=message,
            status=status, seq=seq["n"],
        ))
        db.commit()

    try:
        assessment = db.get(Assessment, assessment_id)
        if assessment is None:
            return
        vendor = db.get(Vendor, assessment.vendor_id)
        org = db.get(Org, assessment.org_id)

        assessment.status = "running"
        db.commit()
        emit("Orchestrator", f"Planning autonomous assessment for {vendor.name}...", "working")

        documents = [
            {
                "doc_type": d.doc_type, "name": d.name, "source": d.source,
                "state": d.state.value if hasattr(d.state, "value") else d.state,
                "issued_at": d.issued_at, "expires_at": d.expires_at,
                "parsed": d.parsed or {}, "url": d.url,
            }
            for d in vendor.documents
        ]

        ctx: dict = {
            "vendor": {
                "name": vendor.name, "website": vendor.website,
                "trust_center_url": vendor.trust_center_url,
                "category": vendor.category, "description": vendor.description,
                "vendor_type": vendor.vendor_type.value if hasattr(vendor.vendor_type, "value") else vendor.vendor_type,
                "data_sensitivity": vendor.data_sensitivity,
                "system_access": vendor.system_access,
                "inherent_tier": vendor.inherent_tier,
            },
            "vendor_key": _domain_key(vendor.website),
            "documents": documents,
            "required_frameworks": list(org.required_frameworks or ["SOC 2", "ISO 27001", "GDPR"]),
            "access_actions": _access_actions_from_documents(documents),
            "findings": [],
            "monitoring": [],
            "tasks": [],
        }

        for agent in CREW:
            agent.run(ctx, emit)

        _persist(db, assessment, vendor, org, ctx)

        assessment.status = "complete"
        assessment.completed_at = datetime.now(UTC)
        db.commit()
        emit("Orchestrator", "Assessment complete. Dashboard and Trust Passport updated.", "done")
    except Exception as e:  # pragma: no cover
        emit("Orchestrator", f"Assessment failed: {e}", "warn")
        a = db.get(Assessment, assessment_id)
        if a:
            a.status = "failed"
            db.commit()
    finally:
        db.close()


def _domain_key(website: str | None) -> str:
    if not website:
        return ""
    from urllib.parse import urlparse
    netloc = urlparse(website).netloc or website
    return netloc.lower().replace("www.", "")


def _persist(db, assessment: Assessment, vendor: Vendor, org: Org, ctx: dict) -> None:
    v = ctx["vendor"]

    # Update vendor profile from intake.
    vendor.category = v.get("category") or vendor.category
    vendor.description = v.get("description") or vendor.description
    vendor.data_sensitivity = v.get("data_sensitivity", vendor.data_sensitivity)
    vendor.system_access = v.get("system_access", vendor.system_access)
    vendor.vendor_type = VendorType(v.get("vendor_type", "saas"))
    vendor.inherent_tier = v.get("inherent_tier", vendor.inherent_tier)
    vendor.status = VendorStatus.monitoring
    if ctx.get("next_review_at"):
        vendor.next_review_at = _parse_date(ctx["next_review_at"])

    # Control results (with evidence citation + observation + gap).
    for c in ctx.get("control_results", []):
        db.add(ControlResult(
            assessment_id=assessment.id, framework=c["framework"],
            control_id=c["control_id"], control_name=c["control_name"],
            status=c["status"], evidence_ref=c.get("evidence_ref"),
            evidence_name=c.get("evidence_name"), citation=c.get("citation", ""),
            observation=c.get("observation", ""), gap=c.get("gap", ""),
            rationale=c.get("rationale", ""),
        ))

    # Findings.
    for f in ctx.get("findings", []):
        db.add(Finding(
            assessment_id=assessment.id, category=f.get("category", "general"),
            severity=f.get("severity", "medium"), title=f.get("title", ""),
            detail=f.get("detail", ""), sources=f.get("sources", []),
        ))

    # Questionnaires.
    for q in ctx.get("questionnaires", []):
        db.add(Questionnaire(
            assessment_id=assessment.id, framework=q["framework"],
            status="complete", answers=q["answers"],
        ))

    # Risk score.
    db.add(RiskScore(
        assessment_id=assessment.id, vendor_id=vendor.id,
        inherent=ctx.get("inherent_score", ctx.get("inherent", 0.0)),
        residual=ctx.get("residual_score", 0.0),
        band=ctx.get("risk_band", "medium"),
        drivers=ctx.get("risk_drivers", []),
        trigger=assessment.trigger,
    ))

    # Monitoring events (replace prior for a clean feed).
    db.query(MonitoringEvent).filter(MonitoringEvent.vendor_id == vendor.id).delete()
    for m in ctx.get("monitoring", []):
        db.add(MonitoringEvent(
            vendor_id=vendor.id, event_type=m.get("event_type", "posture"),
            severity=m.get("severity", "low"), title=m.get("title", ""),
            detail=m.get("detail", ""),
            triggered_rescore=m.get("severity") in ("high", "critical"),
        ))

    # Tasks (replace prior open tasks for this vendor).
    db.query(Task).filter(Task.vendor_id == vendor.id).delete()
    for t in ctx.get("tasks", []):
        db.add(Task(
            vendor_id=vendor.id, assessment_id=assessment.id,
            title=t.get("title", ""), task_type=t.get("task_type", "remediation"),
            owner=t.get("owner"), status=t.get("status", "open"),
            detail=t.get("detail", ""),
        ))

    # Assessment decision + summary.
    assessment.decision = Decision(ctx.get("decision", "pending"))
    assessment.summary = ctx.get("summary", "")

    # Enrich the global Trust Passport (network effect).
    _update_passport(db, vendor, ctx)

    db.commit()


def _update_passport(db, vendor: Vendor, ctx: dict) -> None:
    key = ctx.get("vendor_key") or vendor.name.lower()
    passport = db.query(TrustPassport).filter(TrustPassport.vendor_key == key).first()
    evidence = {
        "documents": ctx.get("documents", []),
        "subprocessors": ctx.get("subprocessors", []),
        "last_residual": ctx.get("residual_score"),
        "coverage": ctx.get("coverage_summary"),
    }
    if passport is None:
        passport = TrustPassport(
            vendor_key=key, name=vendor.name, website=vendor.website,
            category=vendor.category, trust_center_url=vendor.trust_center_url,
            vendor_type=vendor.vendor_type, evidence=evidence, assessments_count=1,
        )
        db.add(passport)
        db.flush()
    else:
        passport.assessments_count += 1
        passport.evidence = evidence
        passport.category = passport.category or vendor.category
    vendor.passport_id = passport.id


def _parse_date(s: str):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None
