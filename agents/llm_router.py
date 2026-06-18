"""
Provider routing for GreenLight AI agents.

LLM_MODE=dev   → all agents route through Gemini (saves Featherless tokens during dev)
LLM_MODE=demo  → each agent uses its assigned provider per blueprint addendum FIX 8

Each agent file calls `get_config(agent_name)` to discover the right base_url, model,
and api_key to use. The Band framework adapter is then constructed around that config.

This module also exposes `load_agent_config()` for Band agent credentials and
`load_prompt()` for system prompts, so individual agent files stay short.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import yaml
from dotenv import load_dotenv

load_dotenv()

LLM_MODE = os.getenv("LLM_MODE", "dev").lower()

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
CONFIG_DIR = REPO_ROOT / "config"


class ProviderConfig(TypedDict):
    base_url: str
    model: str
    api_key: str
    provider: str  # "gemini" | "groq" | "featherless"


_GEMINI = {
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "model": "gemini-2.5-flash",
    "api_key_env": "GOOGLE_API_KEY",
    "provider": "gemini",
}

_GROQ_LLAMA = {
    "base_url": "https://api.groq.com/openai/v1",
    "model": "llama-3.3-70b-versatile",
    "api_key_env": "GROQ_API_KEY",
    "provider": "groq",
}

_GROQ_QWEN = {
    "base_url": "https://api.groq.com/openai/v1",
    "model": "qwen/qwen3-32b",
    "api_key_env": "GROQ_API_KEY",
    "provider": "groq",
}

_FEATHERLESS_LLAMA = {
    "base_url": "https://api.featherless.ai/v1",
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "api_key_env": "FEATHERLESS_API_KEY",
    "provider": "featherless",
}

_FEATHERLESS_DEEPSEEK = {
    "base_url": "https://api.featherless.ai/v1",
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "api_key_env": "FEATHERLESS_API_KEY",
    "provider": "featherless",
}

# Per-mode assignments. Dev mode points every agent at Gemini so the
# 100K Featherless trial only burns during demo recording.
_ASSIGNMENTS: dict[str, dict[str, dict]] = {
    "dev": {
        "default": _GEMINI,
    },
    "demo": {
        "script_analyst": _GEMINI,
        "market_intel":   _GEMINI,
        "red_team":       _GEMINI,
        "budget_auditor": _GROQ_LLAMA,
        "talent_scout":   _GROQ_QWEN,
        "legal_eagle":    _FEATHERLESS_LLAMA,
        "cro":            _FEATHERLESS_DEEPSEEK,
    },
}


def get_config(agent_name: str) -> ProviderConfig:
    """Return the resolved provider config for a given agent in the current mode.

    Resolves the API key from the environment at call time so missing keys fail
    loudly rather than silently routing to a half-configured provider.
    """
    mode_map = _ASSIGNMENTS.get(LLM_MODE)
    if mode_map is None:
        raise ValueError(
            f"Unknown LLM_MODE={LLM_MODE!r}. Expected 'dev' or 'demo'."
        )

    raw = mode_map.get(agent_name) or mode_map.get("default")
    if raw is None:
        raise KeyError(
            f"No provider config for agent {agent_name!r} in LLM_MODE={LLM_MODE!r}"
        )

    key_env = raw["api_key_env"]
    api_key = os.getenv(key_env)
    if not api_key or api_key == "replace-me":
        raise EnvironmentError(
            f"Missing or unset {key_env} for agent {agent_name!r}. "
            f"Edit .env and provide a real key for provider {raw['provider']!r}."
        )

    return {
        "base_url": raw["base_url"],
        "model": raw["model"],
        "api_key": api_key,
        "provider": raw["provider"],
    }


def load_prompt(prompt_name: str) -> str:
    """Load a system prompt from the prompts/ directory."""
    path = PROMPTS_DIR / f"{prompt_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_agent_config(agent_name: str) -> tuple[str, str]:
    """Load Band (agent_id, api_key) from config/agent_config.yaml.

    Returns a (uuid, key) tuple. Raises if the file is missing or the agent name
    is not in it — that means the user hasn't registered the agent on Band yet.
    """
    cfg_path = CONFIG_DIR / "agent_config.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(
            "config/agent_config.yaml not found. "
            "Copy config/agent_config.yaml.example to config/agent_config.yaml "
            "and fill in your Band agent UUIDs and API keys."
        )

    with cfg_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    entry = config.get(agent_name)
    if not entry:
        raise KeyError(
            f"Agent {agent_name!r} not found in agent_config.yaml. "
            f"Register the agent on Band and add its credentials."
        )

    agent_id = entry.get("agent_id")
    api_key = entry.get("api_key")
    if not agent_id or not api_key or "from-band-dashboard" in agent_id:
        raise ValueError(
            f"agent_config.yaml entry for {agent_name!r} has placeholder values. "
            f"Replace with real Band UUID and API key."
        )

    return agent_id, api_key


def band_endpoints() -> tuple[str, str]:
    """Return (ws_url, rest_url) for Band, preferring BAND_* env vars but
    falling back to legacy THENVOI_* names for older SDK versions."""
    ws = (
        os.getenv("BAND_WS_URL")
        or os.getenv("THENVOI_WS_URL")
        or "wss://app.band.ai/api/v1/socket/websocket"
    )
    rest = (
        os.getenv("BAND_REST_URL")
        or os.getenv("THENVOI_REST_URL")
        or "https://app.band.ai"
    )
    return ws, rest
