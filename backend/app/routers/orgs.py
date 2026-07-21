"""Org + settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org, User
from ..schemas import OrgSettingsUpdate
from .deps import get_current_org

router = APIRouter(prefix="/org", tags=["org"])


def _enum(v):
    return v.value if hasattr(v, "value") else v


@router.get("")
def get_org(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    users = db.execute(select(User).where(User.org_id == org.id)).scalars().all()
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "risk_appetite": org.risk_appetite,
        "required_frameworks": org.required_frameworks,
        "users": [{"name": u.name, "email": u.email, "role": _enum(u.role)} for u in users],
    }


@router.put("/settings")
def update_settings(
    body: OrgSettingsUpdate,
    org: Org = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    if body.risk_appetite is not None:
        org.risk_appetite = body.risk_appetite
    if body.required_frameworks is not None:
        org.required_frameworks = body.required_frameworks
    db.commit()
    return {"ok": True, "risk_appetite": org.risk_appetite, "required_frameworks": org.required_frameworks}
