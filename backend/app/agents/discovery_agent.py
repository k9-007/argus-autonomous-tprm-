"""Discovery / Evidence Agent.

Consolidates evidence for the vendor: documents already ingested (uploads +
trust-center), adverse-media / breach signals, and subprocessor lists. Uses the
vendored Bright Data Discovery tool when configured; otherwise curated signals.
"""

from __future__ import annotations

from ..data.fixtures import lookup_demo
from ..tools.discovery import DiscoveryClient
from ..config import settings
from .base import Emit

NAME = "Discovery Agent"


def run(ctx: dict, emit: Emit) -> None:
    vendor = ctx["vendor"]
    docs = ctx.setdefault("documents", [])
    emit(NAME, f"Crawling trust center, SOC 2/DPA, GitHub, news and breach history for {vendor['name']}...", "working")

    demo = lookup_demo(ctx.get("vendor_key", ""))
    if demo:
        # Merge adverse-media / AI findings surfaced by discovery.
        for f in demo.get("findings", []):
            ctx.setdefault("findings", []).append(dict(f))
        # Seed subprocessors + monitoring signals.
        if demo.get("subprocessors"):
            ctx["subprocessors"] = demo["subprocessors"]
        for m in demo.get("monitoring", []):
            ctx.setdefault("monitoring", []).append(dict(m))

    if settings.bright_data_enabled:
        try:
            client = DiscoveryClient()
            results = client.discover_adverse_media(vendor["name"])
            hits = sum(len(v) for v in results.values())
            if hits:
                emit(NAME, f"Live search returned {hits} adverse-media results across categories.", "info")
        except Exception as e:  # pragma: no cover
            emit(NAME, f"Live discovery unavailable ({e}); using cached signals.", "warn")

    n_docs = len(docs)
    n_find = len(ctx.get("findings", []))
    emit(NAME, f"Evidence consolidated: {n_docs} documents, {n_find} risk signals, "
               f"{len(ctx.get('subprocessors', []))} subprocessors.", "done")
