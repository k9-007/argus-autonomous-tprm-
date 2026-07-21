"""Access tool - fetch and extract content from a URL.

Vendored and adapted from Studio1HQ/tprm-agent (MIT) `src/access.py`.
Changes for Argus: uses Bright Data Web Unlocker when configured, otherwise a
plain HTTP fetch; both degrade gracefully so the crew never hard-fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ..config import settings


@dataclass
class ExtractedContent:
    url: str
    title: str
    text: str
    success: bool
    error: Optional[str] = None


class AccessClient:
    def __init__(self):
        self.api_url = "https://api.brightdata.com/request"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.BRIGHT_DATA_API_TOKEN}",
        }

    def fetch_url(self, url: str) -> ExtractedContent:
        try:
            if settings.bright_data_enabled:
                payload = {
                    "zone": settings.BRIGHT_DATA_UNLOCKER_ZONE,
                    "url": url,
                    "format": "raw",
                }
                response = requests.post(
                    self.api_url, headers=self.headers, json=payload, timeout=60
                )
                response.raise_for_status()
                html = response.text
            else:
                response = requests.get(
                    url, timeout=20, headers={"User-Agent": "ArgusTPRM/0.1"}
                )
                response.raise_for_status()
                html = response.text
            return self._extract(html, url)
        except Exception as e:  # pragma: no cover - network dependent
            return ExtractedContent(url=url, title="", text="", success=False, error=str(e))

    def _extract(self, html: str, url: str) -> ExtractedContent:
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        article = soup.find("article") or soup.find("main") or soup.find("body")
        text = article.get_text(separator="\n", strip=True) if article else ""
        return ExtractedContent(url=url, title=title, text=text[:10000], success=True)
