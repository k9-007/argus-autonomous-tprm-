"""Global agent-activity feed - see the crew working across all assessments."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActivityLog, Assessment, Vendor, Org
from .deps import get_current_org

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/recent")
def recent(limit: int = 60, org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    # Assessments for this org.
    assessments = db.execute(
        select(Assessment).where(Assessment.org_id == org.id)
    ).scalars().all()
    a_by_id = {a.id: a for a in assessments}
    vendor_ids = {a.vendor_id for a in assessments}
    vendors = db.execute(select(Vendor).where(Vendor.id.in_(vendor_ids))).scalars().all()
    v_by_id = {v.id: v for v in vendors}

    if not a_by_id:
        return {"running": [], "activity": []}

    rows = db.execute(
        select(ActivityLog)
        .where(ActivityLog.assessment_id.in_(list(a_by_id.keys())))
        .order_by(desc(ActivityLog.created_at))
        .limit(limit)
    ).scalars().all()

    def vendor_name(aid: str) -> str:
        a = a_by_id.get(aid)
        v = v_by_id.get(a.vendor_id) if a else None
        return v.name if v else "Vendor"

    activity = [{
        "assessment_id": r.assessment_id,
        "vendor": vendor_name(r.assessment_id),
        "agent": r.agent,
        "message": r.message,
        "status": r.status,
        "at": r.created_at.isoformat(),
    } for r in rows]

    running = [{
        "assessment_id": a.id,
        "vendor": v_by_id.get(a.vendor_id).name if v_by_id.get(a.vendor_id) else "Vendor",
        "vendor_id": a.vendor_id,
        "status": a.status,
        "trigger": a.trigger,
        "started_at": a.started_at.isoformat(),
    } for a in assessments if a.status in ("queued", "running")]

    return {"running": running, "activity": activity}
