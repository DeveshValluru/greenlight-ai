"""
@RedTeam — Phase 2 adversarial cross-examiner.

Reads all 5 Phase 1 reports, issues formal challenges, tracks resolutions,
and can dynamically recruit @SpecialistOnCall via Band's participant tools.

Framework: Google ADK (via Band's adapter)
Provider:  Gemini 2.5 Flash (free tier)

Run with:  python agents/red_team.py
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
logger = logging.getLogger("red_team")


async def main() -> None:
    agent_id, api_key = load_agent_config("red_team")
    cfg = get_config("red_team")
    ws_url, rest_url = band_endpoints()

    import os
    os.environ.setdefault("GOOGLE_API_KEY", cfg["api_key"])

    adapter = GoogleADKAdapter(
        model=cfg["model"],
        custom_section=load_prompt("red_team"),
        enable_execution_reporting=True,
        # RedTeam needs to see all 5 specialist reports, which are long
        # and may be far back in the room history. Bump both limits.
        max_history_messages=500,
        max_transcript_chars=500_000,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("RedTeam running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
