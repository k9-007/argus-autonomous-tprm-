"""Compliance Agent.

Maps available evidence to controls across the org's required frameworks (plus
ISO 42001 for AI vendors), producing a covered/partial/gap matrix and raising
findings for material gaps. Also verifies evidence freshness/validity.
"""

from __future__ import annotations

from datetime import date, timedelta

from ..compliance.frameworks import map_all, coverage_summary
from .base import Emit

NAME = "Compliance Agent"


_BAD_OPINIONS = {"qualified", "adverse", "disclaimer"}


def _check_freshness(documents: list[dict], emit: Emit) -> list[dict]:
    findings = []
    today = date.today().isoformat()
    seen_expired: set[str] = set()
    for d in documents:
        exp = d.get("expires_at")
        if exp and exp < today:
            name = d.get("name") or d.get("doc_type", "evidence")
            if name in seen_expired:
                continue
            seen_expired.add(name)
            findings.append({
                "category": "compliance_gap", "severity": "high",
                "title": f"Expired evidence: {name}",
                "detail": f"{name} expired on {exp}; a current report is required.",
                "sources": [d.get("url")] if d.get("url") else [],
            })

    # SOC 2 posture is judged across ALL SOC 2 docs, using the strongest one.
    # A vendor often has several artifacts (full report + bridge letter); one weak
    # doc must not override a valid Type II with an unqualified opinion.
    soc2 = [d for d in documents if d.get("doc_type") == "soc2_type2" and (d.get("parsed") or {})]
    if soc2:
        report_types = {(d.get("parsed") or {}).get("report_type") for d in soc2}
        # Only a concern if we have SOC 2 evidence but none of it is Type II.
        if "Type II" not in report_types and report_types == {"Type I"}:
            findings.append({
                "category": "compliance_gap", "severity": "medium",
                "title": "SOC 2 Type I only",
                "detail": "Only a Type I report is available; enterprise buyers require Type II.",
                "sources": [],
            })
        # Flag only genuinely adverse opinions; 'unknown' (e.g. a bridge letter
        # that doesn't restate the opinion) is not a qualification.
        bad = next(
            (str((d.get("parsed") or {}).get("opinion", "")).lower()
             for d in soc2
             if str((d.get("parsed") or {}).get("opinion", "")).lower() in _BAD_OPINIONS),
            None,
        )
        if bad:
            findings.append({
                "category": "compliance_gap", "severity": "high",
                "title": "Qualified SOC 2 opinion",
                "detail": f"Auditor opinion is '{bad}' (not unqualified).",
                "sources": [],
            })
        # An audit report over six months old should be accompanied by a bridge
        # letter covering the gap to today.
        recent_soc2 = [d for d in soc2 if d.get("issued_at") and d["issued_at"] >= (date.today() - timedelta(days=183)).isoformat()]
        has_bridge = any(d.get("doc_type") == "bridge_letter" for d in documents)
        if not recent_soc2 and not has_bridge:
            findings.append({
                "category": "compliance_gap", "severity": "medium",
                "title": "SOC 2 report requires a bridge letter",
                "detail": "Available SOC 2 evidence is more than six months old and no bridge letter was provided.",
                "sources": [],
            })
    for d in documents:
        if d.get("doc_type") == "iso27001" and d.get("state") in ("parsed", "downloaded", "granted", "public"):
            if not (d.get("parsed") or {}).get("accredited_body"):
                findings.append({
                    "category": "compliance_gap", "severity": "low",
                    "title": "ISO 27001 accreditation not verified",
                    "detail": "The certificate does not identify an accredited certification body; analyst validation is required.",
                    "sources": [d.get("url")] if d.get("url") else [],
                })
    return findings


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    documents = ctx.get("documents", [])
    frameworks = list(ctx.get("required_frameworks", ["SOC 2", "ISO 27001", "GDPR"]))
    if vendor.get("vendor_type") in ("ai_agent", "mcp") and "ISO 42001" not in frameworks:
        frameworks.append("ISO 42001")

    emit(NAME, f"Mapping evidence to controls across {', '.join(frameworks)}...", "working")

    control_results = map_all(frameworks, documents)
    ctx["control_results"] = control_results
    summary = coverage_summary(control_results)
    ctx["coverage_summary"] = summary

    # Raise findings for critical gaps (missing SOC2/ISO baseline).
    have_types = {d.get("doc_type") for d in documents if d.get("state") in
                  ("parsed", "downloaded", "granted", "public")}
    if not ({"soc2_type2", "iso27001"} & have_types):
        ctx.setdefault("findings", []).append({
            "category": "compliance_gap", "severity": "high",
            "title": "No SOC 2 Type II or ISO 27001 verified",
            "detail": "No baseline third-party audit evidence is available or accessible.",
            "sources": [],
        })

    fresh_findings = _check_freshness(documents, emit)
    ctx.setdefault("findings", []).extend(fresh_findings)

    emit(NAME, f"Control coverage {summary['coverage_pct']}% - "
               f"{summary['compliant']} compliant, {summary['partial']} partial, "
               f"{summary['gated']} gated, {summary['no_evidence']} no-evidence.", "done")
