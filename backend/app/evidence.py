"""Real evidence ingestion: parse uploaded compliance documents.

Extracts text (PDF via pypdf, or plain text), detects the document type, pulls
issue/expiry dates and an audit opinion, and captures citation snippets used by
the compliance engine to justify each control result.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

# How long each evidence type stays "current" from its issue/period-end date.
_VALIDITY_DAYS = {
    "soc2_type2": 365,
    "soc2_type1": 365,
    "iso27001": 3 * 365,
    "iso42001": 3 * 365,
    "pci_dss": 365,
    "pentest": 365,
}

_DOC_TYPE_SIGNS = {
    "soc2_type2": ["soc 2 type ii", "soc 2 type 2", "type ii report", "trust services criteria"],
    "soc2_type1": ["soc 2 type i", "soc 2 type 1"],
    "iso27001": ["iso/iec 27001", "iso 27001", "statement of applicability"],
    "iso42001": ["iso/iec 42001", "iso 42001", "ai management system"],
    "pci_dss": ["pci dss", "attestation of compliance", "cardholder data"],
    "pentest": ["penetration test", "pentest", "vulnerability assessment"],
    "dpa": ["data processing agreement", "data processing addendum", "standard contractual clauses"],
    "bcdr": ["business continuity", "disaster recovery", "bcp", "rto", "rpo"],
    "baa": ["business associate agreement", "hipaa"],
    "subprocessors": ["subprocessor", "sub-processor"],
    "bridge_letter": ["bridge letter", "period of coverage", "no material changes"],
}

_DATE_RE = re.compile(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})")


def extract_text(filename: str, raw: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        try:
            import io
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def detect_doc_type(filename: str, text: str) -> str:
    hay = (filename + "\n" + text).lower()
    for doc_type, signs in _DOC_TYPE_SIGNS.items():
        if any(s in hay for s in signs):
            return doc_type
    return "other"


def _find_dates(text: str) -> list[str]:
    out = []
    for m in _DATE_RE.finditer(text):
        y, mo, d = m.groups()
        try:
            out.append(date(int(y), int(mo), int(d)).isoformat())
        except ValueError:
            continue
    return sorted(set(out))


def parse_document(filename: str, raw: bytes) -> dict:
    text = extract_text(filename, raw)
    doc_type = detect_doc_type(filename, text)
    lower = text.lower()

    parsed: dict = {"chars": len(text)}
    if doc_type in ("soc2_type2", "soc2_type1"):
        # Trust the doc-type detection first (soc2_type2 is matched on Type II /
        # Trust Services Criteria signals); only call it Type I when the text
        # clearly says so. Avoids defaulting a real Type II report to Type I.
        if doc_type == "soc2_type1":
            parsed["report_type"] = "Type I"
        elif "type ii" in lower or "type 2" in lower:
            parsed["report_type"] = "Type II"
        elif "type i " in lower or "type 1" in lower:
            parsed["report_type"] = "Type I"
        else:
            parsed["report_type"] = "Type II"
        if "unqualified" in lower or "no exceptions" in lower:
            parsed["opinion"] = "unqualified"
        elif "qualified opinion" in lower or "except for" in lower or "adverse opinion" in lower:
            parsed["opinion"] = "qualified"
        else:
            parsed["opinion"] = "unknown"
    if "iso" in doc_type:
        parsed["current"] = "expired" not in lower
        parsed["accredited_body"] = any(term in lower for term in ("accredited", "anab", "ukas", "ias"))
    if doc_type == "bridge_letter":
        parsed["bridges_report"] = "soc" in lower or "audit" in lower

    dates = _find_dates(text)
    # The most recent date is typically the report issue / audit-period end.
    issued_at = dates[-1] if dates else None
    expires_at = None
    if issued_at and doc_type in _VALIDITY_DAYS:
        try:
            y, mo, d = (int(x) for x in issued_at.split("-"))
            expires_at = (date(y, mo, d) + timedelta(days=_VALIDITY_DAYS[doc_type])).isoformat()
        except Exception:
            expires_at = None

    # Citation: first sentence mentioning a control-relevant keyword.
    citation = _first_snippet(text)

    return {
        "doc_type": doc_type,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "parsed": parsed,
        "text_excerpt": text[:4000],
        "citation": citation,
    }


def _first_snippet(text: str, max_len: int = 220) -> str:
    for kw in ("encryption", "access control", "incident", "audit", "control", "security"):
        idx = text.lower().find(kw)
        if idx >= 0:
            start = max(0, idx - 60)
            snippet = " ".join(text[start : start + max_len].split())
            return snippet
    return " ".join(text[:max_len].split())
