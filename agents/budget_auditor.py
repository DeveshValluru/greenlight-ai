"""
@BudgetAuditor — Phase 1 specialist auditing production budgets.

Framework: LangGraph (via Band's adapter)
Provider:  Gemini 2.5 Pro (heavy tier — cross-reference numeric work)

The Groq endpoint is OpenAI-compatible, so we use langchain-openai's
ChatOpenAI with a custom base_url to point at Groq.

Run with:  python agents/budget_auditor.py
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
logger = logging.getLogger("budget_auditor")


async def main() -> None:
    agent_id, api_key = load_agent_config("budget_auditor")
    cfg = get_config("budget_auditor")
    ws_url, rest_url = band_endpoints()

    llm = ChatOpenAI(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=0.2,  # numeric work — low temp
    )

    adapter = LangGraphAdapter(
        llm=llm,
        checkpointer=InMemorySaver(),
        custom_section=load_prompt("budget_auditor"),
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("BudgetAuditor running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
