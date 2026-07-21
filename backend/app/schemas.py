"""Request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    website: HttpUrl | None = None
    trust_center_url: HttpUrl | None = None
    intake_mode: str = "link"  # link | upload | manual
    category: str | None = Field(default=None, max_length=100)
    data_sensitivity: str | None = None  # none/low/medium/high/regulated
    system_access: str | None = None     # none/limited/production
    business_owner: str | None = Field(default=None, max_length=160)

    @field_validator("intake_mode")
    @classmethod
    def validate_intake_mode(cls, value: str) -> str:
        if value not in {"link", "upload", "manual"}:
            raise ValueError("intake_mode must be link, upload, or manual")
        return value


class OrgSettingsUpdate(BaseModel):
    risk_appetite: str | None = None
    required_frameworks: list[str] | None = None


class DocumentIn(BaseModel):
    doc_type: str
    name: str
    issued_at: str | None = None
    expires_at: str | None = None
