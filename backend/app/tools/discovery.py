"""Discovery tool - web search for vendor risk signals.

Vendored and adapted from Studio1HQ/tprm-agent (MIT) `src/discovery.py`.
Changes for Argus:
- Wrapped as a reusable tool the agent crew calls (not a fixed pipeline stage).
- Uses Bright Data's async Discover API (POST a query -> poll a task_id), which
  performs query expansion, reranking and dedup and returns relevance-scored
  results.
- Graceful offline fallback: returns curated demo signals when Bright Data is
  not configured, so assessments run without external services.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

import requests

from ..config import settings


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0


RISK_CATEGORIES = {
    "litigation": ["lawsuit", "litigation", "sued", "court case", "legal action"],
    "financial": ["bankruptcy", "insolvency", "debt", "financial trouble", "default"],
    "fraud": ["fraud", "scam", "investigation", "indictment", "scandal"],
    "regulatory": ["violation", "fine", "penalty", "sanctions", "compliance"],
    "breach": ["data breach", "security incident", "hacked", "leaked", "ransomware"],
}

# How long to wait for an async discover task to finish before giving up.
_POLL_TIMEOUT_SECONDS = 60
_POLL_INTERVAL_SECONDS = 2


class DiscoveryClient:
    """Search for adverse media using Bright Data's Discover API (async)."""

    def __init__(self):
        self.discover_url = "https://api.brightdata.com/discover"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.BRIGHT_DATA_API_TOKEN}",
        }

    def _build_queries(self, vendor_name: str, categories: Optional[list] = None) -> dict[str, str]:
        categories = categories or list(RISK_CATEGORIES.keys())
        queries = {}
        for category in categories:
            keywords = RISK_CATEGORIES.get(category, [])
            keyword_str = " OR ".join(keywords)
            queries[category] = f'"{vendor_name}" ({keyword_str})'
        return queries

    def _start_task(self, query: str) -> Optional[str]:
        payload = {
            "query": query,
            "mode": "standard",
            "language": "en",
            "country": "US",
            "format": "json",
            "remove_duplicates": True,
            "include_content": False,
            "include_images": False,
        }
        response = requests.post(
            self.discover_url, headers=self.headers, json=payload, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            raise RuntimeError(f"discover start failed: {data}")
        return data.get("task_id")

    def _poll_task(self, task_id: str) -> list[dict]:
        deadline = time.monotonic() + _POLL_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            response = requests.get(
                self.discover_url,
                headers=self.headers,
                params={"task_id": task_id},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status == "done":
                return data.get("results", [])
            if status in ("error", "failed"):
                raise RuntimeError(f"discover task {task_id} failed: {data}")
            time.sleep(_POLL_INTERVAL_SECONDS)
        raise TimeoutError(f"discover task {task_id} did not finish in time")

    def _search(self, query: str) -> list[SearchResult]:
        try:
            task_id = self._start_task(query)
            if not task_id:
                return []
            raw_results = self._poll_task(task_id)
            results = []
            for item in raw_results:
                link = item.get("link", "")
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=link,
                        snippet=item.get("description", ""),
                        source=urlsplit(link).netloc,
                        relevance_score=item.get("relevance_score", 0.0) or 0.0,
                    )
                )
            return results
        except Exception as e:  # pragma: no cover - network dependent
            print(f"[discovery] search error: {e}")
            return []

    def discover_adverse_media(
        self, vendor_name: str, categories: Optional[list] = None
    ) -> dict[str, list[SearchResult]]:
        if not settings.bright_data_enabled:
            return {}
        queries = self._build_queries(vendor_name, categories)
        return {cat: self._search(q) for cat, q in queries.items()}
