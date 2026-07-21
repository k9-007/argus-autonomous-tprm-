"""Scheduled review orchestration for the continuous-monitoring lifecycle."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from .agents.orchestrator import run_assessment
from .db import SessionLocal
from .models import Assessment, Vendor, VendorStatus


def run_due_reviews() -> int:
    """Queue and run reviews due today. Safe to call repeatedly from a scheduler."""
    db = SessionLocal()
    try:
        # Existing SQLite deployments use timezone-naive DateTime columns.
        # Keep the scheduler comparison aligned with that persisted format.
        now = datetime.utcnow()
        due = db.execute(
            select(Vendor).where(
                Vendor.status.in_([VendorStatus.monitoring, VendorStatus.renewal]),
                Vendor.next_review_at.is_not(None),
                Vendor.next_review_at <= now,
            )
        ).scalars().all()
        assessment_ids = []
        for vendor in due:
            assessment = Assessment(vendor_id=vendor.id, org_id=vendor.org_id, status="queued", trigger="scheduled_review")
            db.add(assessment)
            vendor.status = VendorStatus.renewal
            db.flush()
            assessment_ids.append(assessment.id)
        db.commit()
    finally:
        db.close()
    for assessment_id in assessment_ids:
        run_assessment(assessment_id)
    return len(assessment_ids)
