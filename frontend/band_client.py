"""
Thin Band REST helper shared by the Streamlit pages.

Reads credentials from Streamlit secrets (preferred) or environment vars
as a fallback so the pages work both deployed and in local dev.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


def _secret(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:  # type: ignore[attr-defined]
            return st.secrets[name]  # type: ignore[index]
    except Exception:
        pass
    return os.getenv(name, default)


BAND_REST_URL = (
    _secret("BAND_REST_URL")
    or _secret("THENVOI_REST_URL")
    or "https://app.band.ai"
).rstrip("/")


def _headers() -> dict[str, str]:
    key = _secret("ORCHESTRATOR_API_KEY") or _secret("BAND_API_KEY")
    if not key:
        raise EnvironmentError(
            "Missing ORCHESTRATOR_API_KEY (or BAND_API_KEY). "
            "Add it to .streamlit/secrets.toml or your environment."
        )
    return {"Authorization": f"Bearer {key}"}


def room_id() -> str:
    rid = _secret("GREENLIGHT_ROOM_ID")
    if not rid:
        raise EnvironmentError(
            "Missing GREENLIGHT_ROOM_ID. Set it after creating the Band room."
        )
    return rid


def fetch_messages() -> list[dict[str, Any]]:
    """Return the room's messages (best-effort across SDK response shapes)."""
    rid = room_id()
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{BAND_REST_URL}/me/chats/{rid}/messages",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
    if isinstance(data, dict):
        return data.get("messages") or data.get("items") or []
    if isinstance(data, list):
        return data
    return []


def post_message(content: str) -> None:
    rid = room_id()
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{BAND_REST_URL}/me/chats/{rid}/messages",
            headers=_headers(),
            json={"content": content},
        )
        resp.raise_for_status()
