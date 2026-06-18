"""
@ScriptAnalyst — Phase 1 specialist analyzing screenplays for production complexity.

Framework: Google ADK (via Band's adapter)
Provider:  Gemini 2.5 Flash (free tier)

Run with:  python agents/script_analyst.py
"""
from __future__ import annotations

import asyncio
import logging

from band import Agent
from band.adapters import GoogleADKAdapter

from agents.llm_router import (
    band_endpoints,
    get_config,
    load_agent_config,
    load_prompt,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("script_analyst")


async def main() -> None:
    agent_id, api_key = load_agent_config("script_analyst")
    cfg = get_config("script_analyst")
    ws_url, rest_url = band_endpoints()

    # google-adk reads GOOGLE_API_KEY from env directly.
    import os
    os.environ.setdefault("GOOGLE_API_KEY", cfg["api_key"])

    adapter = GoogleADKAdapter(
        model=cfg["model"],
        custom_section=load_prompt("script_analyst"),
        enable_execution_reporting=True,
        max_history_messages=200,
        max_transcript_chars=300_000,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("ScriptAnalyst running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
