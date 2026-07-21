"""Seed the demo org, users, and the global Trust Passport network."""

from __future__ import annotations

from sqlalchemy import select

from .db import SessionLocal
from .models import Org, User, Role, TrustPassport, VendorType
from .data.fixtures import passport_seed
from .auth import hash_password

DEMO_ORG_SLUG = "acme"
DEMO_EMAIL = "demo@acme.com"
DEMO_PASSWORD = "demo1234"


def seed() -> None:
    db = SessionLocal()
    try:
        org = db.execute(select(Org).where(Org.slug == DEMO_ORG_SLUG)).scalar_one_or_none()
        if org is None:
            org = Org(
                name="Acme Inc.",
                slug=DEMO_ORG_SLUG,
                risk_appetite="moderate",
                required_frameworks=["SOC 2", "ISO 27001", "GDPR"],
            )
            db.add(org)
            db.flush()
            db.add_all([
                User(org_id=org.id, name="Alex Rivera", email=DEMO_EMAIL, role=Role.admin,
                     password_hash=hash_password(DEMO_PASSWORD)),
                User(org_id=org.id, name="Sam Chen", email="sam@acme.com", role=Role.analyst),
                User(org_id=org.id, name="Jordan Lee", email="jordan@acme.com", role=Role.approver),
            ])

        # Seed the Trust Passport catalogue (idempotent).
        existing = {p.vendor_key for p in db.execute(select(TrustPassport)).scalars().all()}
        for entry in passport_seed():
            if entry["vendor_key"] in existing:
                continue
            db.add(TrustPassport(
                vendor_key=entry["vendor_key"],
                name=entry["name"],
                website=entry.get("website"),
                category=entry.get("category"),
                trust_center_url=entry.get("trust_center_url"),
                vendor_type=VendorType(entry.get("vendor_type", "saas")),
                evidence={},
                assessments_count=0,
            ))
        db.commit()
    finally:
        db.close()
