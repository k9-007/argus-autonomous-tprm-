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


class TaskUpdate(BaseModel):
    status: str | None = None
    owner: str | None = Field(default=None, max_length=160)
    due_date: str | None = None
    detail: str | None = Field(default=None, max_length=6000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {"open", "in_progress", "blocked", "complete", "accepted"}:
            raise ValueError("Invalid task status")
        return value


class UserRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in {"admin", "analyst", "approver", "viewer"}:
            raise ValueError("Invalid role")
        return value


class MonitoringEventIn(BaseModel):
    event_type: str = Field(min_length=2, max_length=100)
    severity: str
    title: str = Field(min_length=2, max_length=240)
    detail: str = Field(default="", max_length=4000)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in {"low", "medium", "high", "critical"}:
            raise ValueError("Invalid severity")
        return value


class DocumentIn(BaseModel):
    doc_type: str
    name: str
    issued_at: str | None = None
    expires_at: str | None = None
