"""LLM access layer.

Wraps the configured reasoning provider (OpenAI GPT-5.6 or Google Gemini,
selected via ARGUS_LLM_PROVIDER). When no API key is configured, callers fall
back to deterministic heuristics so the whole platform runs and demos offline.
"""

from __future__ import annotations

import json
from typing import Any

from .config import settings

_client = None


def _get_client():
    global _client
    if _client is None and settings.llm_enabled:
        if settings.LLM_PROVIDER == "gemini":
            from google import genai

            _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            from openai import OpenAI

            _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def llm_available() -> bool:
    return settings.llm_enabled


def _complete_json_openai(client, system: str, user: str) -> str:
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"


def _complete_json_gemini(client, system: str, user: str) -> str:
    from google.genai import types

    resp = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
        ),
    )
    return resp.text or "{}"


def complete_json(system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """Ask the model for a JSON object. Returns `fallback` if LLM is unavailable
    or the call fails, so callers never crash offline."""
    client = _get_client()
    if client is None:
        return fallback
    try:
        if settings.LLM_PROVIDER == "gemini":
            content = _complete_json_gemini(client, system, user)
        else:
            content = _complete_json_openai(client, system, user)
        return json.loads(content)
    except Exception:
        return fallback
