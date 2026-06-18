"""
@LegalEagle — Phase 1 specialist reviewing IP, guild compliance, and protections.

Framework: LangGraph (via Band's adapter)
Provider:  Gemini 2.5 Pro (legal reasoning needs heavy tier)

Originally wired to PydanticAI, but PydanticAI's strict output validation
caused identity hallucinations and `[[uuid]]` mention leaks. Swapped to
LangGraph for reliable markdown output.

Run with:  python agents/legal_eagle.py
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
logger = logging.getLogger("legal_eagle")


async def main() -> None:
    agent_id, api_key = load_agent_config("legal_eagle")
    cfg = get_config("legal_eagle")
    ws_url, rest_url = band_endpoints()

    llm = ChatOpenAI(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=0.2,  # legal work — low temp for precision
    )

    adapter = LangGraphAdapter(
        llm=llm,
        checkpointer=InMemorySaver(),
        custom_section=load_prompt("legal_eagle"),
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=ws_url,
        rest_url=rest_url,
    )

    logger.info("LegalEagle running on %s (%s). Ctrl+C to stop.", cfg["provider"], cfg["model"])
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
