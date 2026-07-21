"""Portfolio + Trust Passport network dashboards."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org
from .. import services
from .deps import get_current_org

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/portfolio")
def portfolio(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    return services.portfolio(db, org)


@router.get("/passport")
def passport(db: Session = Depends(get_db)):
    return services.passport_network(db)
