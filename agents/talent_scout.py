"""
@TalentScout — Phase 1 specialist evaluating personnel track records.

Framework: LangGraph (via Band's adapter)
Provider:  Groq Qwen3 32B (free tier — separate pool from BudgetAuditor's Llama)

Run with:  python agents/talent_scout.py
"""
from __future__ import annotations

import asyncio
import logging

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from band import Agent
from band.adapters import LangGraphAdapter

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
logger = logging.getLogger("talent_scout")


async def main() -> None:
    agent_id, api_key = load_agent_config("talent_scout")
    cfg = get_config("talent_scout")
    ws_url, rest_url = band_endpoints()

    llm = ChatOpenAI(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=0.3,
    )

    adapter = LangGraphAdapter(
        llm=llm,
        checkpointer=InMemorySaver(),
        custom_section=load_prompt("talent_scout"),
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("TalentScout running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
