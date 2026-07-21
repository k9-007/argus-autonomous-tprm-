"""Trust-center ingestion.

Handles the real-world reality that ~90% of trust centers gate SOC 2 / pen
tests behind request-access + NDA. Strategy:
  1. Detect the platform (Vanta / Conveyor / SafeBase / Whistic / custom).
  2. Ingest public content automatically (certs listed, subprocessors, DPAs).
  3. For gated docs, emit human-authorized access-request + NDA tasks
     (Argus never auto-signs legal terms).
  4. Fall back to a vendor-collaboration invite (the network moat).

For known demo vendors this uses curated fixtures; otherwise it attempts a
best-effort public fetch via the vendored AccessClient.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..data.fixtures import lookup_demo
from .access import AccessClient

_PLATFORM_SIGNATURES = {
    "vanta": ["trust.", "vanta"],
    "conveyor": ["conveyor", "trust.conveyor"],
    "safebase": ["safebase", "security."],
    "whistic": ["whistic"],
}


def detect_platform(url: str | None) -> str:
    if not url:
        return "none"
    host = (urlparse(url).netloc or url).lower()
    if "vanta" in host or host.startswith("trust."):
        return "vanta"
    if "conveyor" in host:
        return "conveyor"
    if "safebase" in host:
        return "safebase"
    if "whistic" in host:
        return "whistic"
    return "custom"


def domain_key(website: str | None) -> str:
    if not website:
        return ""
    netloc = urlparse(website).netloc or website
    return netloc.lower().replace("www.", "")


def ingest(vendor_key: str, trust_center_url: str | None) -> dict:
    """Return ingested evidence + the access actions Argus must take."""
    platform = detect_platform(trust_center_url)
    demo = lookup_demo(vendor_key)

    if demo:
        documents = [dict(d) for d in demo.get("documents", [])]
        subprocessors = demo.get("subprocessors", [])
        notes = f"Ingested {platform} trust center; {len(documents)} documents catalogued."
    else:
        documents, subprocessors, notes = _best_effort_public(trust_center_url, platform)

    # Derive the access actions needed for gated docs.
    access_actions = []
    for d in documents:
        if d.get("state") in ("requested", "nda_pending"):
            action = "sign_nda" if d.get("state") == "nda_pending" else "request_access"
            access_actions.append({
                "doc_type": d.get("doc_type"),
                "doc_name": d.get("name"),
                "action": action,
                "platform": platform,
                "note": (
                    "NDA must be signed by an authorized Approver before download."
                    if action == "sign_nda"
                    else "Access request submitted; awaiting vendor approval."
                ),
            })

    return {
        "platform": platform,
        "documents": documents,
        "subprocessors": subprocessors,
        "access_actions": access_actions,
        "notes": notes,
    }


def _best_effort_public(url: str | None, platform: str) -> tuple[list[dict], list[str], str]:
    """For unknown vendors, fetch public trust-center content best-effort."""
    if not url:
        return [], [], "No trust center provided; will attempt discovery + vendor outreach."
    client = AccessClient()
    content = client.fetch_url(url)
    docs: list[dict] = []
    if content.success:
        text = content.text.lower()
        # Heuristic detection of advertised certifications on the public page.
        if "soc 2" in text or "soc2" in text:
            docs.append({"doc_type": "soc2_type2", "name": "SOC 2 Report (listed)",
                         "source": "trust_center", "state": "nda_pending", "parsed": {}})
        if "iso 27001" in text or "iso27001" in text:
            docs.append({"doc_type": "iso27001", "name": "ISO 27001 Certificate (listed)",
                         "source": "trust_center", "state": "requested", "parsed": {}})
        if "gdpr" in text or "dpa" in text or "data processing" in text:
            docs.append({"doc_type": "dpa", "name": "Data Processing Agreement",
                         "source": "trust_center", "state": "public", "parsed": {"gdpr_scc": True}})
        note = f"Fetched public {platform} trust center; gated documents require access requests."
    else:
        note = f"Could not fetch trust center ({content.error}); falling back to discovery + outreach."
    return docs, [], note
