"""
@CRO (Chief Risk Officer) — Phase 3 synthesizer producing the final scorecard.

Framework: CrewAI (via Band's adapter)
Provider:  Gemini 2.5 Pro — heavy reasoning for weighted-score synthesis

Run with:  python agents/cro.py
"""
from __future__ import annotations

import asyncio
import logging
import os

from band import Agent
from band.adapters import CrewAIAdapter

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
logger = logging.getLogger("cro")


async def main() -> None:
    agent_id, api_key = load_agent_config("cro")
    cfg = get_config("cro")
    ws_url, rest_url = band_endpoints()

    # CrewAI uses LiteLLM. For Gemini: "gemini/<model>" + GEMINI_API_KEY.
    os.environ.setdefault("GEMINI_API_KEY", cfg["api_key"])
    os.environ.setdefault("GOOGLE_API_KEY", cfg["api_key"])
    model_str = f"gemini/{cfg['model']}"

    adapter = CrewAIAdapter(
        model=model_str,
        role="Chief Risk Officer",
        goal=(
            "Synthesize all specialist findings and Phase 2 revisions into a "
            "final GREENLIGHT / CONDITIONAL / PASS verdict."
        ),
        backstory="A 25-year veteran of entertainment finance who delivers data-driven film investment verdicts.",
        custom_section=load_prompt("cro"),
        allow_delegation=False,
        verbose=True,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("CRO running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
