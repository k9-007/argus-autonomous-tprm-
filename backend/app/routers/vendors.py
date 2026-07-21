"""Vendor intake + lifecycle endpoints.

Supports both intake modes: upload compliance docs, or provide a trust-center
link. On add, evidence is ingested and an autonomous assessment is kicked off in
the background so the client can stream the crew working live.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    Vendor, Assessment, Document, TrustPassport, AuditLog,
    VendorType, VendorStatus, DocState, Org,
)
from ..schemas import VendorCreate, DocumentIn
from ..tools import trust_center
from ..data.fixtures import lookup_demo
from ..agents.orchestrator import run_assessment
from .. import evidence as evidence_mod
from .. import services
from .deps import get_current_org

router = APIRouter(prefix="/vendors", tags=["vendors"])


def _domain_key(website: str | None, trust_url: str | None) -> str:
    key = trust_center.domain_key(website)
    if key:
        return key
    if trust_url:
        return trust_center.domain_key(trust_url)
    return ""


def _ingest_documents(vendor: Vendor, mode: str, vendor_key: str, db: Session) -> None:
    """Populate Document rows based on intake mode."""
    docs: list[dict] = []
    if vendor.trust_center_url:
        ingest = trust_center.ingest(vendor_key, vendor.trust_center_url)
        docs = ingest["documents"]
    elif mode == "upload":
        demo = lookup_demo(vendor_key)
        if demo:
            # Simulate that the customer uploaded their vendor's compliance pack.
            for d in demo.get("documents", []):
                dd = dict(d)
                dd["source"] = "upload"
                if dd.get("state") in ("requested", "nda_pending"):
                    dd["state"] = "parsed"  # uploaded copies are already accessible
                docs.append(dd)
    for d in docs:
        db.add(Document(
            vendor_id=vendor.id, org_id=vendor.org_id,
            doc_type=d.get("doc_type", "other"), name=d.get("name", "Document"),
            source=d.get("source", "trust_center"),
            state=DocState(d.get("state", "parsed")),
            url=d.get("url"), issued_at=d.get("issued_at"), expires_at=d.get("expires_at"),
            parsed=d.get("parsed", {}),
        ))


@router.post("")
def create_vendor(
    body: VendorCreate,
    background: BackgroundTasks,
    org: Org = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    website = body.website
    if not website and body.trust_center_url:
        # Derive a website guess from the trust-center domain.
        website = body.trust_center_url

    vendor_key = _domain_key(website, body.trust_center_url)
    demo = lookup_demo(vendor_key)

    vendor = Vendor(
        org_id=org.id,
        name=body.name,
        website=website,
        trust_center_url=body.trust_center_url or (demo.get("trust_center_url") if demo else None),
        category=body.category or (demo.get("category") if demo else None),
        vendor_type=VendorType((demo.get("vendor_type") if demo else None) or "saas"),
        data_sensitivity=body.data_sensitivity or "unknown",
        system_access=body.system_access or "unknown",
        intake_mode=body.intake_mode,
        business_owner=body.business_owner,
        status=VendorStatus.assessing,
    )
    # Link to an existing passport if present.
    if vendor_key:
        passport = db.execute(
            select(TrustPassport).where(TrustPassport.vendor_key == vendor_key)
        ).scalars().first()
        if passport:
            vendor.passport_id = passport.id
    db.add(vendor)
    db.flush()

    _ingest_documents(vendor, body.intake_mode, vendor_key, db)

    assessment = Assessment(vendor_id=vendor.id, org_id=org.id, status="queued", trigger="onboarding")
    db.add(assessment)
    db.add(AuditLog(org_id=org.id, actor="user", action="vendor.add",
                    target=vendor.name, detail=f"intake_mode={body.intake_mode}"))
    db.commit()

    background.add_task(run_assessment, assessment.id)

    return {"vendor_id": vendor.id, "assessment_id": assessment.id, "status": "queued"}


@router.get("")
def list_vendors(org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    vendors = db.execute(select(Vendor).where(Vendor.org_id == org.id)).scalars().all()
    return {"vendors": [services.vendor_row(db, v) for v in vendors]}


@router.get("/{vendor_id}")
def get_vendor(vendor_id: str, org: Org = Depends(get_current_org), db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.org_id != org.id:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return services.vendor_detail(db, vendor)


@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: str, org: Org = Depends(get_current_org), db: Session = Depends(get_db)
):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.org_id != org.id:
        raise HTTPException(status_code=404, detail="Vendor not found")
    name = vendor.name
    db.delete(vendor)  # cascades documents, assessments, monitoring, tasks
    db.add(AuditLog(org_id=org.id, actor="user", action="vendor.delete", target=name))
    db.commit()
    return {"ok": True, "deleted": vendor_id}


@router.post("/{vendor_id}/documents")
def add_document(
    vendor_id: str, body: DocumentIn,
    org: Org = Depends(get_current_org), db: Session = Depends(get_db),
):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.org_id != org.id:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.add(Document(
        vendor_id=vendor.id, org_id=org.id, doc_type=body.doc_type, name=body.name,
        source="upload", state=DocState.parsed, issued_at=body.issued_at, expires_at=body.expires_at,
    ))
    db.commit()
    return {"ok": True}


@router.post("/{vendor_id}/upload")
async def upload_documents(
    vendor_id: str,
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    org: Org = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """Real document upload: parse each file, detect type, extract dates + citation."""
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.org_id != org.id:
        raise HTTPException(status_code=404, detail="Vendor not found")

    parsed_docs = []
    for f in files:
        raw = await f.read()
        info = evidence_mod.parse_document(f.filename or "document", raw)
        db.add(Document(
            vendor_id=vendor.id, org_id=org.id,
            doc_type=info["doc_type"], name=f.filename or info["doc_type"],
            source="upload", state=DocState.parsed,
            issued_at=info.get("issued_at"), expires_at=info.get("expires_at"),
            parsed={**info.get("parsed", {}), "citation": info.get("citation", "")},
        ))
        parsed_docs.append({"name": f.filename, "doc_type": info["doc_type"]})

    # Kick off a fresh assessment now that new evidence is available.
    assessment = Assessment(vendor_id=vendor.id, org_id=org.id, status="queued", trigger="new_evidence")
    db.add(assessment)
    db.add(AuditLog(org_id=org.id, actor="user", action="documents.upload",
                    target=vendor.name, detail=f"{len(parsed_docs)} file(s)"))
    db.commit()
    background.add_task(run_assessment, assessment.id)
    return {"uploaded": parsed_docs, "assessment_id": assessment.id}


@router.post("/{vendor_id}/assess")
def reassess(
    vendor_id: str, background: BackgroundTasks,
    org: Org = Depends(get_current_org), db: Session = Depends(get_db),
):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.org_id != org.id:
        raise HTTPException(status_code=404, detail="Vendor not found")
    assessment = Assessment(vendor_id=vendor.id, org_id=org.id, status="queued", trigger="rescore")
    db.add(assessment)
    db.commit()
    background.add_task(run_assessment, assessment.id)
    return {"assessment_id": assessment.id, "status": "queued"}
