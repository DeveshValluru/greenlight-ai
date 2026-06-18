"""
Provider routing for GreenLight AI agents.

Multi-model architecture — each agent uses a model matched to its workload:

  Workload tier         Model                                        Why
  ─────────────────────────────────────────────────────────────────────────────
  Heavy reasoning       Gemini 2.5 Pro                               Cross-agent
                                                                     numeric
                                                                     reconciliation,
                                                                     adversarial
                                                                     forensics
  Light reasoning       Gemini 2.5 Flash                             Document parse,
                                                                     knowledge
                                                                     retrieval,
                                                                     personnel lookup
  Domain (legal)        Featherless Llama 3.3 70B Instruct          Legal/compliance
                                                                     domain coverage +
                                                                     partner-prize
                                                                     eligibility
  Domain (verdict)      Featherless DeepSeek R1 Distill 70B         Structured
                                                                     reasoning for
                                                                     weighted-score
                                                                     synthesis

Provider count:   2 (Gemini + Featherless)
Distinct models:  4 (Flash, Pro, Llama 70B, DeepSeek R1)

If FEATHERLESS_API_KEY is not set, the two Featherless agents fall back to
Gemini Flash automatically so local dev never blocks on a paid key.

Each agent file calls `get_config(<short_name>)` to discover its model and
credentials. The Band framework adapter is then constructed around the
returned config.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"
CONFIG_DIR = REPO_ROOT / "config"


class ProviderConfig(TypedDict):
    base_url: str
    model: str
    api_key: str
    provider: str       # "gemini" | "featherless"
    workload_tier: str  # "heavy" | "light" | "domain"


# ----- Model definitions -----

_GEMINI_FLASH = {
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "model": "gemini-2.5-flash",
    "api_key_env": "GOOGLE_API_KEY",
    "provider": "gemini",
    "workload_tier": "light",
}

_GEMINI_PRO = {
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "model": "gemini-2.5-pro",
    "api_key_env": "GOOGLE_API_KEY",
    "provider": "gemini",
    "workload_tier": "heavy",
}

_FEATHERLESS_LLAMA = {
    "base_url": "https://api.featherless.ai/v1",
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "api_key_env": "FEATHERLESS_API_KEY",
    "provider": "featherless",
    "workload_tier": "domain",
}

_FEATHERLESS_DEEPSEEK = {
    "base_url": "https://api.featherless.ai/v1",
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "api_key_env": "FEATHERLESS_API_KEY",
    "provider": "featherless",
    "workload_tier": "domain",
}


# ----- Per-agent assignments -----

_ASSIGNMENTS: dict[str, dict] = {
    # Phase 1 specialists
    "script_analyst": _GEMINI_FLASH,         # parse + structure a screenplay
    "budget_auditor": _GEMINI_PRO,           # cross-reference VFX, locations, days
    "market_intel":   _GEMINI_FLASH,         # knowledge retrieval of comps
    "legal_eagle":    _FEATHERLESS_LLAMA,    # legal domain coverage
    "talent_scout":   _GEMINI_FLASH,         # personnel evaluation
    # Phase 2 adversary
    "red_team":       _GEMINI_PRO,           # heavy reasoning across all 5 reports
    # Phase 3 synthesizer
    "cro":            _FEATHERLESS_DEEPSEEK, # structured weighted scoring
}


def _fallback_if_missing_key(raw: dict) -> dict:
    """If a Featherless slot is configured but FEATHERLESS_API_KEY is unset,
    fall back to Gemini Flash so dev still works."""
    if raw["provider"] != "featherless":
        return raw
    if os.getenv("FEATHERLESS_API_KEY") and os.getenv("FEATHERLESS_API_KEY") != "replace-me":
        return raw
    return _GEMINI_FLASH


def get_config(agent_name: str) -> ProviderConfig:
    """Return the resolved provider config for a given agent.

    Resolves the API key from the environment at call time so missing keys
    fail loudly rather than silently routing to a half-configured provider.
    """
    raw = _ASSIGNMENTS.get(agent_name)
    if raw is None:
        raise KeyError(
            f"No provider config for agent {agent_name!r}. "
            f"Add a row to _ASSIGNMENTS in agents/llm_router.py."
        )

    raw = _fallback_if_missing_key(raw)

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
        "workload_tier": raw["workload_tier"],
    }


def load_prompt(prompt_name: str) -> str:
    """Load a system prompt from the prompts/ directory."""
    path = PROMPTS_DIR / f"{prompt_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_agent_config(agent_name: str) -> tuple[str, str]:
    """Load Band (agent_id, api_key) from config/agent_config.yaml."""
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
    """Return (ws_url, rest_url) for Band."""
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
