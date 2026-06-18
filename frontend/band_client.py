"""
Thin Band REST helper shared by the Streamlit pages.

Strategy:
  * READ (Debate / Scorecard pages): use one of our AGENT API keys to call
    the agent endpoint /api/v1/agent/chats/{id}/messages — that endpoint is
    confirmed working from the running agent processes.
  * WRITE (Upload page): we don't post from Streamlit. Instead, the Upload
    page builds the kickoff text and copies it to the user's clipboard.
    The user pastes into the Band UI manually. This is the honest UX given
    Band's human-API write endpoint requires a tier we don't have.

Credentials come from Streamlit secrets first, then .env in the project root.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st
import yaml
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


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


def _agent_credentials() -> tuple[str, str]:
    """Return (agent_id, api_key) of an agent to read messages with.

    Picks the first available entry from config/agent_config.yaml — any agent
    that is a participant in the room can read its history via the agent API.
    """
    cfg_path = _PROJECT_ROOT / "config" / "agent_config.yaml"
    if not cfg_path.exists():
        raise EnvironmentError(
            "config/agent_config.yaml not found. Streamlit needs an agent's "
            "credentials to read room messages."
        )
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    for short_name in ("script_analyst", "budget_auditor", "market_intel",
                       "legal_eagle", "talent_scout", "red_team", "cro"):
        entry = cfg.get(short_name) or {}
        agent_id = entry.get("agent_id")
        api_key = entry.get("api_key")
        if agent_id and api_key and "from-band-dashboard" not in agent_id:
            return agent_id, api_key
    raise EnvironmentError(
        "No agent credentials found in agent_config.yaml. Register agents on "
        "Band and paste their UUIDs + API keys into the file."
    )


def room_id(phase: str = "briefing") -> str:
    """Resolve the Band room ID for a phase (with single-room fallback)."""
    by_phase = {
        "briefing":   "BRIEFING_ROOM_ID",
        "cross_exam": "CROSS_EXAM_ROOM_ID",
        "verdict":    "VERDICT_ROOM_ID",
    }
    for var in (by_phase.get(phase), "GREENLIGHT_ROOM_ID"):
        if not var:
            continue
        val = _secret(var)
        if val:
            return val
    raise EnvironmentError(
        "Missing a Band room ID. Set GREENLIGHT_ROOM_ID in .env "
        "(single-room mode) or one of BRIEFING_ROOM_ID / CROSS_EXAM_ROOM_ID / "
        "VERDICT_ROOM_ID (breakout mode)."
    )


def fetch_messages(phase: str = "briefing", limit: int = 100) -> list[dict[str, Any]]:
    """Read messages from a Band room using an agent's API key.

    Hits /api/v1/agent/chats/{id}/messages — confirmed working endpoint.
    """
    rid = room_id(phase)
    _, agent_api_key = _agent_credentials()
    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{BAND_REST_URL}/api/v1/agent/chats/{rid}/messages",
            headers={"X-API-Key": agent_api_key},
            params={"limit": limit},
        )
        resp.raise_for_status()
        data = resp.json()
    if isinstance(data, dict):
        return data.get("messages") or data.get("items") or data.get("data") or []
    if isinstance(data, list):
        return data
    return []


def copy_to_clipboard(text: str) -> bool:
    """Best-effort cross-platform clipboard copy. Returns True on success."""
    if sys.platform == "win32":
        try:
            subprocess.run(["clip.exe"], input=text.encode("utf-8"), check=True)
            return True
        except Exception:
            return False
    if sys.platform == "darwin":
        try:
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
        except Exception:
            return False
    # linux — try xclip then xsel
    for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
        try:
            subprocess.run(cmd, input=text.encode("utf-8"), check=True)
            return True
        except Exception:
            continue
    return False
