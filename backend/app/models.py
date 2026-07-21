"""Multi-tenant data model for Argus.

Hierarchy: Org -> Users -> Vendors -> Assessments -> (Findings, Questionnaires,
RiskScores, Documents, MonitoringEvents, Tasks). A global TrustPassport is shared
across orgs and enriched by every assessment (the network-effect moat).
"""

from datetime import datetime, UTC
import enum
import uuid

from sqlalchemy import (
    String,
    Integer,
    Float,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class Role(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    approver = "approver"  # authorized to sign NDAs / accept risk
    viewer = "viewer"


class VendorType(str, enum.Enum):
    saas = "saas"
    ai_agent = "ai_agent"
    mcp = "mcp"


class VendorStatus(str, enum.Enum):
    intake = "intake"
    assessing = "assessing"
    monitoring = "monitoring"
    renewal = "renewal"
    offboarded = "offboarded"


class Decision(str, enum.Enum):
    approve = "approve"
    approve_with_conditions = "approve_with_conditions"
    block = "block"
    pending = "pending"


class DocState(str, enum.Enum):
    public = "public"
    requested = "requested"
    nda_pending = "nda_pending"
    granted = "granted"
    downloaded = "downloaded"
    parsed = "parsed"
    expired = "expired"


class Org(Base):
    __tablename__ = "orgs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    risk_appetite: Mapped[str] = mapped_column(String, default="moderate")
    required_frameworks: Mapped[list] = mapped_column(
        JSON, default=lambda: ["SOC 2", "ISO 27001", "GDPR"]
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    users: Mapped[list["User"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    vendors: Mapped[list["Vendor"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("orgs.id"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.analyst)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    token: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    org: Mapped[Org] = relationship(back_populates="users")


class TrustPassport(Base):
    """Global, cross-org vendor profile. Reused/dedup'd by vendor_key (domain)."""

    __tablename__ = "trust_passports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vendor_key: Mapped[str] = mapped_column(String, unique=True, index=True)  # normalized domain
    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor_type: Mapped[VendorType] = mapped_column(SAEnum(VendorType), default=VendorType.saas)
    trust_center_url: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)  # cached public evidence
    assessments_count: Mapped[int] = mapped_column(Integer, default=0)
    vendor_claimed: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("orgs.id"), index=True)
    passport_id: Mapped[str | None] = mapped_column(ForeignKey("trust_passports.id"), nullable=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    trust_center_url: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor_type: Mapped[VendorType] = mapped_column(SAEnum(VendorType), default=VendorType.saas)

    data_sensitivity: Mapped[str] = mapped_column(String, default="unknown")  # none/low/medium/high/regulated
    system_access: Mapped[str] = mapped_column(String, default="unknown")  # none/limited/production
    inherent_tier: Mapped[int] = mapped_column(Integer, default=3)  # 1 (critical) .. 4 (low)

    status: Mapped[VendorStatus] = mapped_column(SAEnum(VendorStatus), default=VendorStatus.intake)
    intake_mode: Mapped[str] = mapped_column(String, default="link")  # upload | link | manual
    business_owner: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    org: Mapped[Org] = relationship(back_populates="vendors")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    monitoring_events: Mapped[list["MonitoringEvent"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    org_id: Mapped[str] = mapped_column(String, index=True)

    doc_type: Mapped[str] = mapped_column(String)  # soc2_type2, iso27001, dpa, pentest, ...
    name: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, default="upload")  # upload | trust_center | vendor
    state: Mapped[DocState] = mapped_column(SAEnum(DocState), default=DocState.parsed)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    issued_at: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    vendor: Mapped[Vendor] = relationship(back_populates="documents")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    org_id: Mapped[str] = mapped_column(String, index=True)

    status: Mapped[str] = mapped_column(String, default="queued")  # queued/running/complete/failed
    decision: Mapped[Decision] = mapped_column(SAEnum(Decision), default=Decision.pending)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str] = mapped_column(String, default="onboarding")

    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    vendor: Mapped[Vendor] = relationship(back_populates="assessments")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    questionnaires: Mapped[list["Questionnaire"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    activity: Mapped[list["ActivityLog"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    controls: Mapped[list["ControlResult"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    category: Mapped[str] = mapped_column(String)  # litigation, breach, ai_risk, compliance_gap...
    severity: Mapped[str] = mapped_column(String, default="medium")  # low/medium/high/critical
    title: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(Text, default="")
    sources: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    assessment: Mapped[Assessment] = relationship(back_populates="findings")


class ControlResult(Base):
    """Per-control mapping result across frameworks.

    status: compliant | partially_compliant | no_evidence | gated | expired |
            not_applicable | needs_review
    Every result carries the evidence artifact it was judged against (name +
    citation) and an observation, matching how real compliance agents document.
    """

    __tablename__ = "control_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    framework: Mapped[str] = mapped_column(String)
    control_id: Mapped[str] = mapped_column(String)
    control_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="no_evidence")
    evidence_ref: Mapped[str | None] = mapped_column(String, nullable=True)  # doc_type
    evidence_name: Mapped[str | None] = mapped_column(String, nullable=True)  # document name
    citation: Mapped[str] = mapped_column(Text, default="")  # snippet / section
    observation: Mapped[str] = mapped_column(Text, default="")
    gap: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")

    assessment: Mapped[Assessment] = relationship(back_populates="controls")


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    framework: Mapped[str] = mapped_column(String)  # SIG Lite, CAIQ v4
    status: Mapped[str] = mapped_column(String, default="complete")
    answers: Mapped[list] = mapped_column(JSON, default=list)  # [{q, answer, evidence, confidence}]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    assessment: Mapped[Assessment] = relationship(back_populates="questionnaires")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    vendor_id: Mapped[str] = mapped_column(String, index=True)

    inherent: Mapped[float] = mapped_column(Float, default=0.0)
    residual: Mapped[float] = mapped_column(Float, default=0.0)
    band: Mapped[str] = mapped_column(String, default="medium")
    drivers: Mapped[list] = mapped_column(JSON, default=list)  # [{factor, impact, detail}]
    trigger: Mapped[str] = mapped_column(String, default="assessment")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    assessment: Mapped[Assessment] = relationship(back_populates="scores")


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    event_type: Mapped[str] = mapped_column(String)  # cve, breach, cert_expiry, domain, github_leak, subprocessor
    severity: Mapped[str] = mapped_column(String, default="medium")
    title: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(Text, default="")
    triggered_rescore: Mapped[bool] = mapped_column(default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    vendor: Mapped[Vendor] = relationship(back_populates="monitoring_events")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    assessment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    task_type: Mapped[str] = mapped_column(String, default="remediation")  # remediation | access_request | nda | exception
    owner: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")
    due_date: Mapped[str | None] = mapped_column(String, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    vendor: Mapped[Vendor] = relationship(back_populates="tasks")


class ActivityLog(Base):
    """Streamed crew activity feed for a running assessment."""

    __tablename__ = "activity_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id"), index=True)
    agent: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="info")  # info | working | done | warn
    seq: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    assessment: Mapped[Assessment] = relationship(back_populates="activity")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(String, index=True)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str | None] = mapped_column(String, nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
