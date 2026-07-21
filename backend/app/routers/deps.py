"""Shared router dependencies for bearer-token authentication and tenant isolation."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org, User


def _token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    token = _token_from_header(authorization)
    if not token:
        return None
    return db.execute(select(User).where(User.token == token)).scalar_one_or_none()


def get_current_org(
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Org:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    org = db.get(Org, user.org_id)
    if org is None:
        raise HTTPException(status_code=401, detail="Organization not found")
    return org


def require_roles(*roles: str):
    """Return a dependency enforcing least-privilege operations per workspace."""
    def dependency(user: User | None = Depends(get_current_user)) -> User:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        role = user.role.value if hasattr(user.role, "value") else user.role
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")
        return user
    return dependency
