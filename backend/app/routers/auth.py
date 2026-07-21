"""Auth endpoints: signup (creates an org + admin user), login, me."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org, User, Role
from ..auth import hash_password, verify_password, new_token
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    name: str
    email: str
    password: str
    org_name: str


class LoginBody(BaseModel):
    email: str
    password: str


def _slugify(s: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "org"
    return base


def _user_payload(user: User, org: Org) -> dict:
    return {
        "token": user.token,
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role.value},
        "org": {"id": org.id, "name": org.name, "slug": org.slug,
                "required_frameworks": org.required_frameworks, "risk_appetite": org.risk_appetite},
    }


@router.post("/signup")
def signup(body: SignupBody, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    slug = _slugify(body.org_name)
    n = 1
    base_slug = slug
    while db.execute(select(Org).where(Org.slug == slug)).scalar_one_or_none():
        n += 1
        slug = f"{base_slug}-{n}"

    org = Org(name=body.org_name, slug=slug,
              required_frameworks=["SOC 2", "ISO 27001", "GDPR"], risk_appetite="moderate")
    db.add(org)
    db.flush()
    user = User(
        org_id=org.id, name=body.name, email=body.email.lower(), role=Role.admin,
        password_hash=hash_password(body.password), token=new_token(),
    )
    db.add(user)
    db.commit()
    return _user_payload(user, org)


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.token = new_token()
    db.commit()
    org = db.get(Org, user.org_id)
    return _user_payload(user, org)


@router.get("/me")
def me(user: User | None = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    org = db.get(Org, user.org_id)
    return _user_payload(user, org)
