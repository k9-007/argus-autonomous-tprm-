"""Request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class VendorCreate(BaseModel):
    name: str
    website: str | None = None
    trust_center_url: str | None = None
    intake_mode: str = "link"  # link | upload | manual
    category: str | None = None
    data_sensitivity: str | None = None  # none/low/medium/high/regulated
    system_access: str | None = None     # none/limited/production
    business_owner: str | None = None


class OrgSettingsUpdate(BaseModel):
    risk_appetite: str | None = None
    required_frameworks: list[str] | None = None


class DocumentIn(BaseModel):
    doc_type: str
    name: str
    issued_at: str | None = None
    expires_at: str | None = None
