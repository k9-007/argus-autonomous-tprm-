"""Portfolio + Trust Passport network dashboards."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Org
from .. import services
from .deps import get_current_org

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/portfolio")
def portfolio(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    return services.portfolio(db, org)


@router.get("/portfolio/export.csv")
def export_portfolio(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    """Board-ready, portable portfolio snapshot for spreadsheet/PDF workflows."""
    portfolio_data = services.portfolio(db, org)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Vendor", "Category", "Tier", "Inherent risk", "Residual risk", "Risk band", "Decision", "Status", "Next review"])
    for row in portfolio_data["vendors"]:
        writer.writerow([row["name"], row["category"], row["tier"], row["inherent"], row["residual"], row["band"], row["decision"], row["status"], row["next_review_at"]])
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=argus-portfolio.csv"})


@router.get("/passport")
def passport(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    return services.passport_network(db)
