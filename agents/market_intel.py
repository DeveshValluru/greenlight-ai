"""
@MarketIntel — Phase 1 specialist researching comparable films and ROI projections.

Framework: Google ADK (via Band's adapter)
Provider:  Gemini 2.5 Flash (free tier)

Run with:  python agents/market_intel.py
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
logger = logging.getLogger("market_intel")


async def main() -> None:
    agent_id, api_key = load_agent_config("market_intel")
    cfg = get_config("market_intel")
    ws_url, rest_url = band_endpoints()

    import os
    os.environ.setdefault("GOOGLE_API_KEY", cfg["api_key"])

    adapter = GoogleADKAdapter(
        model=cfg["model"],
        custom_section=load_prompt("market_intel"),
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

    logger.info("MarketIntel running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
