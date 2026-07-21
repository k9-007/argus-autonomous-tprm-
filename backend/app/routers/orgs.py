"""Org + settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org, User, Role, AuditLog
from ..schemas import OrgSettingsUpdate, UserRoleUpdate
from .deps import get_current_org, require_roles

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
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if body.risk_appetite is not None:
        org.risk_appetite = body.risk_appetite
    if body.required_frameworks is not None:
        org.required_frameworks = body.required_frameworks
    db.add(AuditLog(org_id=org.id, actor=actor.email, action="org.settings.update", target=org.name))
    db.commit()
    return {"ok": True, "risk_appetite": org.risk_appetite, "required_frameworks": org.required_frameworks}


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    body: UserRoleUpdate,
    org: Org = Depends(get_current_org),
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None or user.org_id != org.id:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = Role(body.role)
    db.add(AuditLog(org_id=org.id, actor=actor.email, action="user.role.update", target=user.email, detail=body.role))
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role.value}


@router.get("/audit")
def audit_log(
    limit: int = 100,
    org: Org = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    rows = db.execute(select(AuditLog).where(AuditLog.org_id == org.id).order_by(desc(AuditLog.created_at)).limit(min(max(limit, 1), 250))).scalars().all()
    return {"activity": [{"id": row.id, "actor": row.actor, "action": row.action, "target": row.target, "detail": row.detail, "at": row.created_at.isoformat()} for row in rows]}
