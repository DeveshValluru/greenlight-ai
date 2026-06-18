"""
Provider routing for GreenLight AI agents.

Single provider (Gemini), three model tiers — each agent uses a model
matched to its workload:

  Tier            Model                          Why
  ─────────────────────────────────────────────────────────────────────────────
  Lite            gemini-2.5-flash-lite          Light lookups, short outputs
                                                 (TalentScout person eval,
                                                  MarketIntel comp retrieval)
  Standard        gemini-2.5-flash               Document parse + structured
                                                 output (ScriptAnalyst)
  Heavy           gemini-2.5-pro                 Cross-agent numerical
                                                 reasoning, adversarial
                                                 forensics, weighted synthesis
                                                 (BudgetAuditor, LegalEagle,
                                                  RedTeam, CRO)

Provider count:   1 (Gemini)
Distinct models:  3 (flash-lite, flash, pro)

All seven agents authenticate to the same Gemini OpenAI-compatible endpoint
with a single GOOGLE_API_KEY, but the per-agent model selection means we
spend Pro tokens only on heavy reasoning and lite tokens on simple lookups.
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
    provider: str       # "gemini"
    workload_tier: str  # "lite" | "standard" | "heavy"


# ----- Model definitions (all Gemini via OpenAI-compatible endpoint) -----

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"
_GEMINI_KEY_ENV = "GOOGLE_API_KEY"

_GEMINI_LITE = {
    "base_url": _GEMINI_BASE,
    "model": "gemini-2.5-flash-lite",
    "api_key_env": _GEMINI_KEY_ENV,
    "provider": "gemini",
    "workload_tier": "lite",
}

_GEMINI_FLASH = {
    "base_url": _GEMINI_BASE,
    "model": "gemini-2.5-flash",
    "api_key_env": _GEMINI_KEY_ENV,
    "provider": "gemini",
    "workload_tier": "standard",
}

_GEMINI_PRO = {
    "base_url": _GEMINI_BASE,
    "model": "gemini-2.5-pro",
    "api_key_env": _GEMINI_KEY_ENV,
    "provider": "gemini",
    "workload_tier": "heavy",
}


# ----- Per-agent assignments -----

_ASSIGNMENTS: dict[str, dict] = {
    # Phase 1 specialists
    "script_analyst": _GEMINI_FLASH,    # parse + structure a screenplay
    "budget_auditor": _GEMINI_PRO,      # cross-reference VFX, locations, days
    "market_intel":   _GEMINI_LITE,     # lookup comparable films
    "legal_eagle":    _GEMINI_PRO,      # legal/compliance reasoning
    "talent_scout":   _GEMINI_LITE,     # personnel evaluation
    # Phase 2 adversary
    "red_team":       _GEMINI_PRO,      # heavy reasoning across all 5 reports
    # Phase 3 synthesizer
    "cro":            _GEMINI_PRO,      # weighted-score synthesis + verdict
}


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

    key_env = raw["api_key_env"]
    api_key = os.getenv(key_env)
    if not api_key or api_key == "replace-me":
        raise EnvironmentError(
            f"Missing or unset {key_env} for agent {agent_name!r}. "
            f"Add a real Gemini API key to .env."
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
