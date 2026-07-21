"""Serialization + aggregation helpers shared by routers."""

from __future__ import annotations

from datetime import date
from collections import Counter

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .models import (
    Vendor, Assessment, RiskScore, Finding, ControlResult, Questionnaire,
    MonitoringEvent, Task, Org, TrustPassport,
)


def _enum(v):
    return v.value if hasattr(v, "value") else v


def latest_assessment(db: Session, vendor_id: str) -> Assessment | None:
    return db.execute(
        select(Assessment).where(Assessment.vendor_id == vendor_id).order_by(desc(Assessment.started_at))
    ).scalars().first()


def latest_score(db: Session, assessment_id: str) -> RiskScore | None:
    return db.execute(
        select(RiskScore).where(RiskScore.assessment_id == assessment_id).order_by(desc(RiskScore.created_at))
    ).scalars().first()


def vendor_row(db: Session, vendor: Vendor) -> dict:
    a = latest_assessment(db, vendor.id)
    score = latest_score(db, a.id) if a else None
    return {
        "id": vendor.id,
        "name": vendor.name,
        "category": vendor.category,
        "vendor_type": _enum(vendor.vendor_type),
        "tier": vendor.inherent_tier,
        "status": _enum(vendor.status),
        "inherent": score.inherent if score else None,
        "residual": score.residual if score else None,
        "band": score.band if score else None,
        "decision": _enum(a.decision) if a else "pending",
        "assessment_id": a.id if a else None,
        "assessment_status": a.status if a else None,
        "next_review_at": vendor.next_review_at.isoformat() if vendor.next_review_at else None,
        "created_at": vendor.created_at.isoformat(),
    }


def vendor_detail(db: Session, vendor: Vendor) -> dict:
    a = latest_assessment(db, vendor.id)
    score = latest_score(db, a.id) if a else None

    documents = [{
        "id": d.id, "doc_type": d.doc_type, "name": d.name, "source": d.source,
        "state": _enum(d.state), "issued_at": d.issued_at, "expires_at": d.expires_at,
        "parsed": d.parsed, "url": d.url,
    } for d in vendor.documents]

    findings = []
    controls = []
    questionnaires = []
    if a:
        findings = [{
            "category": f.category, "severity": f.severity, "title": f.title,
            "detail": f.detail, "sources": f.sources,
        } for f in db.execute(select(Finding).where(Finding.assessment_id == a.id)).scalars().all()]
        controls = [{
            "framework": c.framework, "control_id": c.control_id, "control_name": c.control_name,
            "status": c.status, "evidence_ref": c.evidence_ref, "evidence_name": c.evidence_name,
            "citation": c.citation, "observation": c.observation, "gap": c.gap,
        } for c in db.execute(select(ControlResult).where(ControlResult.assessment_id == a.id)).scalars().all()]
        questionnaires = [{
            "framework": q.framework, "status": q.status, "answers": q.answers,
        } for q in db.execute(select(Questionnaire).where(Questionnaire.assessment_id == a.id)).scalars().all()]

    monitoring = [{
        "event_type": m.event_type, "severity": m.severity, "title": m.title,
        "detail": m.detail, "triggered_rescore": m.triggered_rescore,
        "detected_at": m.detected_at.isoformat(),
    } for m in db.execute(
        select(MonitoringEvent).where(MonitoringEvent.vendor_id == vendor.id).order_by(desc(MonitoringEvent.detected_at))
    ).scalars().all()]

    # Residual-risk history across all assessments (oldest -> newest) for trend charts.
    score_history = [{
        "residual": s.residual, "inherent": s.inherent, "band": s.band,
        "trigger": s.trigger, "at": s.created_at.isoformat(),
    } for s in db.execute(
        select(RiskScore).where(RiskScore.vendor_id == vendor.id).order_by(RiskScore.created_at)
    ).scalars().all()]

    tasks = [{
        "id": t.id, "title": t.title, "task_type": t.task_type, "owner": t.owner,
        "status": t.status, "detail": t.detail, "due_date": t.due_date,
    } for t in db.execute(select(Task).where(Task.vendor_id == vendor.id)).scalars().all()]

    # Framework coverage rollup (weighted, matching the compliance engine).
    from .compliance.frameworks import coverage_summary as _cov
    coverage = {}
    by_fw: dict[str, list] = {}
    for c in controls:
        by_fw.setdefault(c["framework"], []).append(c)
    for fw, ctrls in by_fw.items():
        coverage[fw] = _cov(ctrls)

    return {
        "id": vendor.id,
        "name": vendor.name,
        "website": vendor.website,
        "trust_center_url": vendor.trust_center_url,
        "category": vendor.category,
        "description": vendor.description,
        "vendor_type": _enum(vendor.vendor_type),
        "data_sensitivity": vendor.data_sensitivity,
        "system_access": vendor.system_access,
        "tier": vendor.inherent_tier,
        "status": _enum(vendor.status),
        "intake_mode": vendor.intake_mode,
        "next_review_at": vendor.next_review_at.isoformat() if vendor.next_review_at else None,
        "assessment": {
            "id": a.id, "status": a.status, "decision": _enum(a.decision),
            "summary": a.summary, "started_at": a.started_at.isoformat(),
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        } if a else None,
        "score": {
            "inherent": score.inherent, "residual": score.residual,
            "band": score.band, "drivers": score.drivers,
        } if score else None,
        "documents": documents,
        "findings": findings,
        "controls": controls,
        "coverage": coverage,
        "questionnaires": questionnaires,
        "monitoring": monitoring,
        "score_history": score_history,
        "tasks": tasks,
        "subprocessors": _passport_subprocessors(db, vendor),
    }


def _passport_subprocessors(db: Session, vendor: Vendor) -> list:
    if not vendor.passport_id:
        return []
    p = db.get(TrustPassport, vendor.passport_id)
    if p and p.evidence:
        return p.evidence.get("subprocessors", [])
    return []


def portfolio(db: Session, org: Org) -> dict:
    vendors = db.execute(select(Vendor).where(Vendor.org_id == org.id)).scalars().all()
    rows = [vendor_row(db, v) for v in vendors]

    bands = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for r in rows:
        if r["band"]:
            bands[r["band"]] = bands.get(r["band"], 0) + 1

    top = sorted([r for r in rows if r["residual"] is not None],
                 key=lambda r: r["residual"], reverse=True)[:10]
    today = date.today().isoformat()
    overdue = [r for r in rows if r["next_review_at"] and r["next_review_at"][:10] < today]
    concentration = Counter((r["category"] or "Unclassified") for r in rows)
    heatmap = [{"tier": tier, "band": band, "count": sum(1 for r in rows if r["tier"] == tier and r["band"] == band)}
               for tier in range(1, 5) for band in ("critical", "high", "medium", "low")]

    # Expiring evidence across the portfolio (expired or within 90 days).
    expiring = []
    for v in vendors:
        for d in v.documents:
            if d.expires_at and d.expires_at <= _plus_days(90):
                expiring.append({
                    "vendor": v.name, "document": d.name,
                    "expires_at": d.expires_at,
                    "expired": d.expires_at < today,
                })

    return {
        "org": {"name": org.name, "risk_appetite": org.risk_appetite,
                "required_frameworks": org.required_frameworks},
        "counts": {
            "total": len(rows),
            "by_band": bands,
            "monitoring": sum(1 for r in rows if r["status"] == "monitoring"),
            "tier1": sum(1 for r in rows if r["tier"] == 1),
        },
        "vendors": rows,
        "top_risky": top,
        "analytics": {
            "overdue_reviews": len(overdue),
            "concentration": [{"category": category, "count": count} for category, count in concentration.most_common(8)],
            "heatmap": heatmap,
        },
        "expiring_evidence": expiring,
    }


def _plus_days(n: int) -> str:
    from datetime import timedelta
    return (date.today() + timedelta(days=n)).isoformat()


def passport_network(db: Session) -> dict:
    passports = db.execute(
        select(TrustPassport).order_by(desc(TrustPassport.assessments_count))
    ).scalars().all()
    return {
        "total": len(passports),
        "assessed": sum(1 for p in passports if p.assessments_count > 0),
        "claimed": sum(1 for p in passports if p.vendor_claimed),
        "passports": [{
            "name": p.name, "vendor_key": p.vendor_key, "category": p.category,
            "vendor_type": _enum(p.vendor_type), "assessments_count": p.assessments_count,
            "claimed": p.vendor_claimed,
            # Residual scores are tenant-contextual and intentionally never shared.
            "last_residual": None,
        } for p in passports[:100]],
    }
