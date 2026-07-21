"""Assessment status + live activity feed (polling + SSE)."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from ..db import get_db, SessionLocal
from ..models import Assessment, ActivityLog

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _enum(v):
    return v.value if hasattr(v, "value") else v


def _activity_dict(r: ActivityLog) -> dict:
    return {
        "seq": r.seq, "agent": r.agent, "message": r.message,
        "status": r.status, "at": r.created_at.isoformat(),
    }


@router.get("/{assessment_id}")
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    a = db.get(Assessment, assessment_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {
        "id": a.id, "vendor_id": a.vendor_id, "status": a.status,
        "decision": _enum(a.decision), "summary": a.summary,
        "trigger": a.trigger, "started_at": a.started_at.isoformat(),
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
    }


@router.get("/{assessment_id}/activity")
def get_activity(assessment_id: str, after: int = 0, db: Session = Depends(get_db)):
    rows = db.execute(
        select(ActivityLog)
        .where(ActivityLog.assessment_id == assessment_id, ActivityLog.seq > after)
        .order_by(ActivityLog.seq)
    ).scalars().all()
    a = db.get(Assessment, assessment_id)
    return {
        "status": a.status if a else "unknown",
        "activity": [_activity_dict(r) for r in rows],
    }


@router.get("/{assessment_id}/stream")
async def stream_activity(assessment_id: str):
    async def event_gen():
        last = 0
        while True:
            db = SessionLocal()
            try:
                rows = db.execute(
                    select(ActivityLog)
                    .where(ActivityLog.assessment_id == assessment_id, ActivityLog.seq > last)
                    .order_by(ActivityLog.seq)
                ).scalars().all()
                a = db.get(Assessment, assessment_id)
                status = a.status if a else "unknown"
                payloads = [_activity_dict(r) for r in rows]
            finally:
                db.close()

            for p in payloads:
                last = p["seq"]
                yield {"event": "activity", "data": json.dumps(p)}

            if status in ("complete", "failed") and not payloads:
                yield {"event": "done", "data": json.dumps({"status": status})}
                break
            await asyncio.sleep(0.4)

    return EventSourceResponse(event_gen())
