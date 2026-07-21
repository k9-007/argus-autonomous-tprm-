"""Framework control catalogs + evidence-to-control mapping.

Representative control subsets across the frameworks buyers care about in 2026:
SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS, NIST CSF, and ISO 42001 (AI governance).
Each control declares the evidence that satisfies it; the mapper marks each
control covered / partial / gap with a rationale and evidence reference.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Control:
    control_id: str
    name: str
    satisfied_by: list[str]  # doc_types that cover this control
    partial_by: list[str]    # doc_types that partially cover


# Evidence "flags" that can also satisfy controls (parsed from documents).
# e.g. a DPA with SCCs, a listed subprocessor page, etc.

FRAMEWORKS: dict[str, list[Control]] = {
    "SOC 2": [
        Control("CC1.0", "Control Environment / Governance", ["soc2_type2", "iso27001"], []),
        Control("CC6.1", "Logical Access Controls", ["soc2_type2"], ["iso27001"]),
        Control("CC6.6", "Encryption in Transit & At Rest", ["soc2_type2"], ["pentest"]),
        Control("CC7.2", "Security Monitoring & Detection", ["soc2_type2"], ["pentest"]),
        Control("CC7.4", "Incident Response", ["soc2_type2"], []),
        Control("CC9.2", "Vendor / Subprocessor Management", ["soc2_type2", "subprocessors"], ["dpa"]),
        Control("A1.2", "Availability / BCP-DR", ["soc2_type2", "bcdr"], []),
    ],
    "ISO 27001": [
        Control("A.5", "Information Security Policies", ["iso27001", "soc2_type2"], []),
        Control("A.8", "Asset Management", ["iso27001"], ["soc2_type2"]),
        Control("A.9", "Access Control", ["iso27001", "soc2_type2"], []),
        Control("A.12", "Operations Security", ["iso27001"], ["pentest"]),
        Control("A.16", "Incident Management", ["iso27001", "soc2_type2"], []),
        Control("A.17", "Business Continuity", ["iso27001", "bcdr"], []),
    ],
    "GDPR": [
        Control("Art.28", "Data Processor Obligations (DPA)", ["dpa"], []),
        Control("Art.32", "Security of Processing", ["soc2_type2", "iso27001"], ["pentest"]),
        Control("Art.44", "International Transfers (SCCs)", ["dpa"], []),
        Control("Art.30", "Records of Processing / Subprocessors", ["subprocessors", "dpa"], []),
    ],
    "HIPAA": [
        Control("164.308", "Administrative Safeguards", ["soc2_type2", "iso27001"], []),
        Control("164.312", "Technical Safeguards (Encryption/Access)", ["soc2_type2"], ["pentest"]),
        Control("BAA", "Business Associate Agreement", ["baa", "dpa"], []),
    ],
    "PCI DSS": [
        Control("PCI-1", "Cardholder Data Protection (AoC)", ["pci_dss"], []),
        Control("PCI-11", "Regular Security Testing", ["pentest", "pci_dss"], []),
    ],
    "NIST CSF": [
        Control("ID", "Identify (Asset & Risk Mgmt)", ["iso27001", "soc2_type2"], []),
        Control("PR", "Protect (Access, Data Security)", ["soc2_type2", "iso27001"], []),
        Control("DE", "Detect (Monitoring)", ["soc2_type2"], ["pentest"]),
        Control("RS", "Respond (Incident Response)", ["soc2_type2", "iso27001"], []),
    ],
    "ISO 42001": [  # AI management system
        Control("AI.5", "AI Governance & Accountability", ["iso42001", "ai_policy"], []),
        Control("AI.6", "AI Risk Assessment", ["iso42001", "ai_policy"], []),
        Control("AI.8", "Data Governance for Training/Inference", ["iso42001", "dpa"], []),
        Control("AI.9", "Transparency & Human Oversight", ["iso42001", "ai_policy"], []),
    ],
}


from datetime import date

USABLE_STATES = {"parsed", "downloaded", "granted", "public"}
GATED_STATES = {"nda_pending", "requested"}

# Human-readable citation templates per evidence type (what an analyst would note).
_CITATION = {
    "soc2_type2": "SOC 2 Type II, Section IV (Trust Services Criteria) - control tested and operating effectively over the audit period.",
    "soc2_type1": "SOC 2 Type I, Section III - control design assessed at a point in time (operating effectiveness not tested).",
    "iso27001": "ISO/IEC 27001 Statement of Applicability - Annex A control implemented and certified.",
    "iso42001": "ISO/IEC 42001 AI management system - governance control documented.",
    "pci_dss": "PCI DSS Attestation of Compliance - requirement validated by QSA.",
    "pentest": "Penetration test report - testing performed; findings remediated.",
    "dpa": "Data Processing Agreement - clause present (incl. SCCs where applicable).",
    "bcdr": "Business continuity / DR plan - documented and tested.",
    "subprocessors": "Subprocessor register - fourth parties disclosed and current.",
    "baa": "Business Associate Agreement - HIPAA obligations contractually bound.",
}


def _is_expired(d: dict) -> bool:
    exp = d.get("expires_at")
    return bool(exp and exp < date.today().isoformat())


def _match(doc_types: list[str], documents: list[dict]):
    """Return (usable_doc, gated_doc, expired_doc) matching any of doc_types."""
    usable = gated = expired = None
    for d in documents:
        if d.get("doc_type") not in doc_types:
            continue
        state = d.get("state")
        if state in USABLE_STATES and not _is_expired(d):
            usable = usable or d
        elif state in USABLE_STATES and _is_expired(d):
            expired = expired or d
        elif state in GATED_STATES:
            gated = gated or d
    return usable, gated, expired


def _citation_for(doc: dict) -> str:
    # Prefer a real extracted snippet when the doc was uploaded/parsed.
    if doc.get("citation"):
        return doc["citation"]
    parsed = doc.get("parsed") or {}
    if parsed.get("citation"):
        return parsed["citation"]
    return _CITATION.get(doc.get("doc_type"), "Referenced in provided evidence.")


def map_framework(framework: str, documents: list[dict]) -> list[dict]:
    controls = FRAMEWORKS.get(framework, [])
    results = []
    for c in controls:
        need = ", ".join(c.satisfied_by) or "attestation"
        sat_usable, sat_gated, sat_expired = _match(c.satisfied_by, documents)
        par_usable, par_gated, par_expired = _match(c.partial_by, documents)

        status = "no_evidence"
        doc = None
        observation = ""
        gap = ""

        if sat_usable:
            status, doc = "compliant", sat_usable
            observation = f"Verified in {doc.get('name')}: {_citation_for(doc)}"
        elif par_usable:
            status, doc = "partially_compliant", par_usable
            observation = (f"Partial: related evidence in {par_usable.get('name')}, "
                           f"but the primary artifact ({need}) was not provided.")
            gap = f"Provide {need} to fully satisfy this control."
        elif sat_gated or par_gated:
            status, doc = "gated", (sat_gated or par_gated)
            observation = (f"Evidence exists in the vendor's trust center but is gated "
                           f"({doc.get('state')}). Access requested / NDA pending.")
            gap = "Complete trust-center access request to verify."
        elif sat_expired or par_expired:
            status, doc = "expired", (sat_expired or par_expired)
            observation = f"{doc.get('name')} is expired ({doc.get('expires_at')}); a current report is required."
            gap = f"Obtain a current {need}."
        else:
            status = "no_evidence"
            observation = "No evidence provided; control claim unverified (treated as non-compliant)."
            gap = f"Provide {need}."

        results.append({
            "framework": framework,
            "control_id": c.control_id,
            "control_name": c.name,
            "status": status,
            "evidence_ref": doc.get("doc_type") if doc else None,
            "evidence_name": doc.get("name") if doc else None,
            "citation": _citation_for(doc) if doc else "",
            "observation": observation,
            "gap": gap,
            "rationale": observation,
        })
    return results


def map_all(frameworks: list[str], documents: list[dict]) -> list[dict]:
    out: list[dict] = []
    for fw in frameworks:
        out.extend(map_framework(fw, documents))
    return out


# Weighting for coverage: compliant=1, partial=0.5, gated=0.25 (verifiable soon), else 0.
_WEIGHT = {"compliant": 1.0, "partially_compliant": 0.5, "gated": 0.25,
           "expired": 0.1, "needs_review": 0.25, "not_applicable": 0.0, "no_evidence": 0.0}


def coverage_summary(control_results: list[dict]) -> dict:
    total = len(control_results) or 1
    def count(s): return sum(1 for c in control_results if c["status"] == s)
    scored = sum(_WEIGHT.get(c["status"], 0.0) for c in control_results)
    applicable = sum(1 for c in control_results if c["status"] != "not_applicable") or 1
    return {
        "total": len(control_results),
        "compliant": count("compliant"),
        "partial": count("partially_compliant"),
        "gated": count("gated"),
        "expired": count("expired"),
        "no_evidence": count("no_evidence"),
        "not_applicable": count("not_applicable"),
        # legacy keys kept for any older callers
        "covered": count("compliant"),
        "gap": count("no_evidence"),
        "coverage_pct": round(100 * scored / applicable, 1),
    }
