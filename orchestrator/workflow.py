"""
GreenLight AI — breakout-room orchestrator.

3-room architecture:

    BRIEFING (5 specialists + human)
       ↓ orchestrator forwards each specialist's full report
    CROSS-EXAMINATION (RedTeam + 5 specialists for defense)
       ↓ orchestrator forwards the 5 reports + RedTeam's summary
    VERDICT (CRO alone with curated inputs)
       ↓ CRO posts the final scorecard

Each phase room only sees what it needs. The audit trail still exists —
every message in every room is logged by Band — but each agent operates
on a clean, curated context.

Run with:
    python -m orchestrator.workflow

Required env vars:
    BAND_REST_URL                 — Band REST base URL
    ORCHESTRATOR_API_KEY          — your user API key
    BRIEFING_ROOM_ID              — Phase 1 room
    CROSS_EXAM_ROOM_ID            — Phase 2 room
    VERDICT_ROOM_ID               — Phase 3 room

Backwards compat:
    GREENLIGHT_ROOM_ID            — if set and the breakout vars are not,
                                    falls back to single-room mode (legacy).
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import yaml
from dotenv import load_dotenv

load_dotenv()

# Load agent UUIDs from config so we can populate the `mentions` array on
# trigger messages (RedTeam, CRO, etc.).
_CONFIG_PATH = (
    __import__("pathlib").Path(__file__).resolve().parent.parent
    / "config" / "agent_config.yaml"
)
try:
    with _CONFIG_PATH.open(encoding="utf-8") as _f:
        _AGENT_CFG = yaml.safe_load(_f) or {}
except FileNotFoundError:
    _AGENT_CFG = {}


def _agent_uuid(short_name: str) -> str | None:
    entry = _AGENT_CFG.get(short_name) or {}
    return entry.get("agent_id")


def _mention(short_name: str, display: str) -> dict | None:
    uid = _agent_uuid(short_name)
    if not uid:
        return None
    return {
        "id": uid,
        "name": display,
        "handle": f"Devesh Valluru/{short_name.replace('_', '')}",
    }

BAND_REST_URL = (
    os.getenv("BAND_REST_URL")
    or os.getenv("THENVOI_REST_URL")
    or "https://app.band.ai"
).rstrip("/")
BAND_API_KEY = os.getenv("ORCHESTRATOR_API_KEY")

BRIEFING_ROOM_ID = os.getenv("BRIEFING_ROOM_ID") or os.getenv("GREENLIGHT_ROOM_ID")
CROSS_EXAM_ROOM_ID = os.getenv("CROSS_EXAM_ROOM_ID") or BRIEFING_ROOM_ID
VERDICT_ROOM_ID = os.getenv("VERDICT_ROOM_ID") or BRIEFING_ROOM_ID

SINGLE_ROOM_MODE = (BRIEFING_ROOM_ID == CROSS_EXAM_ROOM_ID == VERDICT_ROOM_ID)

POLL_INTERVAL_SECS = 5
PHASE1_TIMEOUT_SECS = 600
MAX_REMINDERS_PER_AGENT = 2

PHASE1_MARKERS: dict[str, str] = {
    "ScriptAnalyst":  "FEASIBILITY SCORE",
    "BudgetAuditor":  "BUDGET ADEQUACY SCORE",
    "MarketIntel":    "COMMERCIAL VIABILITY SCORE",
    "LegalEagle":     "LEGAL RISK SCORE",
    "TalentScout":    "TALENT RISK SCORE",
}
PHASE2_MARKER = "CROSS-EXAMINATION SUMMARY"
PHASE3_MARKER = "VERDICT:"

BAND_USER = "Devesh Valluru"

PHASE2_TRIGGER_TEMPLATE = (
    "All 5 specialist reports are now posted above. "
    "@{user}/redteam — please run your full cross-examination per your prompt. "
    "Issue formal challenges (C-1, C-2, …), track resolutions, and post your "
    "CROSS-EXAMINATION SUMMARY when complete."
)
PHASE3_TRIGGER_TEMPLATE = (
    "Cross-examination is complete. @{user}/cro — please synthesize "
    "all findings (Phase 2 revisions take precedence over Phase 1 originals) "
    "and post the final GreenLight scorecard + verdict."
)
RETRY_MESSAGE = (
    "@{user}/{handle} your Phase 1 report has not been received yet. "
    "Please post your analysis following the standard format."
)
AGENT_HANDLES = {
    "ScriptAnalyst":  "scriptanalyst",
    "BudgetAuditor":  "budgetauditor",
    "MarketIntel":    "marketintel",
    "LegalEagle":     "legaleagle",
    "TalentScout":    "talentscout",
}

log = logging.getLogger("greenlight.orchestrator")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)


@dataclass
class CapturedReport:
    agent: str
    sender: str | None
    content: str
    timestamp: str | None = None


@dataclass
class PhaseState:
    started_at: float = field(default_factory=time.time)
    reports: dict[str, CapturedReport] = field(default_factory=dict)
    reminders: dict[str, int] = field(default_factory=dict)


def _require_env() -> None:
    missing = [name for name, val in [
        ("ORCHESTRATOR_API_KEY", BAND_API_KEY),
        ("BRIEFING_ROOM_ID (or GREENLIGHT_ROOM_ID)", BRIEFING_ROOM_ID),
    ] if not val]
    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}. "
            f"Set them in .env before running the orchestrator."
        )


def _endpoint(room_id: str) -> str:
    return f"{BAND_REST_URL}/api/v1/me/chats/{room_id}/messages"


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": BAND_API_KEY, "content-type": "application/json"}


async def fetch_messages(client: httpx.AsyncClient, room_id: str) -> list[dict[str, Any]]:
    """Pull recent messages from a Band room (user-side endpoint)."""
    try:
        resp = await client.get(_endpoint(room_id), headers=_auth_headers(), timeout=15)
        if resp.status_code != 200:
            log.warning("fetch_messages %s → %s", room_id[:8], resp.status_code)
            return []
        data = resp.json()
        if isinstance(data, dict):
            return data.get("messages") or data.get("items") or data.get("data") or []
        if isinstance(data, list):
            return data
    except httpx.HTTPError as exc:
        log.warning("fetch_messages %s error: %s", room_id[:8], exc)
    return []


async def post_message(
    client: httpx.AsyncClient,
    room_id: str,
    content: str,
    mentions: list[dict] | None = None,
) -> bool:
    """POST a message into a Band room as the orchestrator user.

    Band's POST body shape:
        {"message": {"content": "...", "mentions": [{"id": "...", ...}, ...]}}
    """
    log.info("orchestrator → %s: %s", room_id[:8], _truncate(content, 100))
    payload = {"message": {"content": content, "mentions": mentions or []}}
    try:
        resp = await client.post(
            _endpoint(room_id),
            headers=_auth_headers(),
            json=payload,
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return True
        log.error("POST %s failed: %s — %s", room_id[:8], resp.status_code, resp.text[:300])
    except httpx.HTTPError as exc:
        log.error("POST %s exception: %s", room_id[:8], exc)
    return False


def _truncate(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _sender(msg: dict) -> str:
    return (msg.get("sender_name") or msg.get("sender") or "").lstrip("@")


def _content(msg: dict) -> str:
    return msg.get("content") or msg.get("text") or ""


def _find_report_message(
    messages: list[dict], agent_name: str, marker: str
) -> CapturedReport | None:
    """Find the most recent message that looks like the named agent's report."""
    for m in reversed(messages):
        content = _content(m)
        sender = _sender(m)
        if marker in content and (
            sender.lower().startswith(agent_name.lower())
            or agent_name.lower() in sender.lower()
        ):
            return CapturedReport(
                agent=agent_name,
                sender=sender,
                content=content,
                timestamp=m.get("inserted_at") or m.get("timestamp"),
            )
    # Fall back: any message with the marker, regardless of sender (the agent
    # may sign with display name, full handle, or nothing).
    for m in reversed(messages):
        content = _content(m)
        if marker in content:
            return CapturedReport(
                agent=agent_name,
                sender=_sender(m),
                content=content,
                timestamp=m.get("inserted_at") or m.get("timestamp"),
            )
    return None


async def _phase1_loop(client: httpx.AsyncClient, state: PhaseState) -> bool:
    """Watch Briefing room until all 5 reports are captured. Returns True when done."""
    messages = await fetch_messages(client, BRIEFING_ROOM_ID)
    if not messages:
        return False

    for agent, marker in PHASE1_MARKERS.items():
        if agent in state.reports:
            continue
        report = _find_report_message(messages, agent, marker)
        if report:
            state.reports[agent] = report
            log.info("  ✅ Captured %s report (%d/5)", agent, len(state.reports))

    if len(state.reports) >= 5:
        return True

    elapsed = time.time() - state.started_at
    if elapsed > PHASE1_TIMEOUT_SECS:
        for agent in PHASE1_MARKERS:
            if agent in state.reports:
                continue
            if state.reminders.get(agent, 0) >= MAX_REMINDERS_PER_AGENT:
                continue
            log.warning("  ⏰ Timeout — reminding %s", agent)
            short = {
                "ScriptAnalyst": "script_analyst",
                "BudgetAuditor": "budget_auditor",
                "MarketIntel":   "market_intel",
                "LegalEagle":    "legal_eagle",
                "TalentScout":   "talent_scout",
            }[agent]
            m = _mention(short, agent)
            await post_message(
                client,
                BRIEFING_ROOM_ID,
                RETRY_MESSAGE.format(user=BAND_USER, handle=AGENT_HANDLES[agent]),
                mentions=[m] if m else [],
            )
            state.reminders[agent] = state.reminders.get(agent, 0) + 1
    return False


async def _forward_reports_to_cross_exam(
    client: httpx.AsyncClient, state: PhaseState
) -> None:
    """Repost each captured Phase 1 report into the Cross-Exam room as a fresh
    message, in a clean order, then trigger RedTeam."""
    if SINGLE_ROOM_MODE:
        log.info("single-room mode — no forwarding, just triggering RedTeam in place")
        await post_message(
            client,
            CROSS_EXAM_ROOM_ID,
            PHASE2_TRIGGER_TEMPLATE.format(user=BAND_USER),
        )
        return

    log.info("🔁 Forwarding 5 reports to Cross-Examination room")
    order = ["ScriptAnalyst", "BudgetAuditor", "MarketIntel", "LegalEagle", "TalentScout"]
    for agent in order:
        report = state.reports.get(agent)
        if not report:
            log.warning("  ⚠️  %s report missing — forwarding placeholder", agent)
            content = f"📋 **{agent} report — NOT DELIVERED in Phase 1.**"
        else:
            content = (
                f"📋 **{agent} report (forwarded from Briefing)**\n\n{report.content}"
            )
        await post_message(client, CROSS_EXAM_ROOM_ID, content)
        await asyncio.sleep(1)  # spacing so the chat reads cleanly

    redteam_mention = _mention("red_team", "RedTeam")
    await post_message(
        client,
        CROSS_EXAM_ROOM_ID,
        PHASE2_TRIGGER_TEMPLATE.format(user=BAND_USER),
        mentions=[redteam_mention] if redteam_mention else [],
    )


async def _phase2_loop(client: httpx.AsyncClient) -> str | None:
    """Watch Cross-Exam room until RedTeam posts its summary.
    Returns the captured summary content, or None if still waiting."""
    messages = await fetch_messages(client, CROSS_EXAM_ROOM_ID)
    for m in reversed(messages):
        content = _content(m)
        sender = _sender(m).lower()
        if PHASE2_MARKER in content and "redteam" in sender:
            return content
    # tolerate any sender as a fallback
    for m in reversed(messages):
        content = _content(m)
        if PHASE2_MARKER in content:
            return content
    return None


async def _forward_to_verdict(
    client: httpx.AsyncClient,
    state: PhaseState,
    cross_exam_summary: str,
) -> None:
    """Forward 5 reports + RedTeam summary into the Verdict room."""
    if SINGLE_ROOM_MODE:
        log.info("single-room mode — no forwarding, just triggering CRO in place")
        await post_message(
            client,
            VERDICT_ROOM_ID,
            PHASE3_TRIGGER_TEMPLATE.format(user=BAND_USER),
        )
        return

    log.info("🔁 Forwarding reports + RedTeam summary to Verdict room")
    order = ["ScriptAnalyst", "BudgetAuditor", "MarketIntel", "LegalEagle", "TalentScout"]
    for agent in order:
        report = state.reports.get(agent)
        if not report:
            await post_message(
                client,
                VERDICT_ROOM_ID,
                f"📋 **{agent} report — NOT DELIVERED.**",
            )
            continue
        await post_message(
            client,
            VERDICT_ROOM_ID,
            f"📋 **{agent} report (forwarded)**\n\n{report.content}",
        )
        await asyncio.sleep(1)

    await post_message(
        client,
        VERDICT_ROOM_ID,
        f"🔴 **RedTeam cross-examination summary (forwarded)**\n\n{cross_exam_summary}",
    )
    await asyncio.sleep(1)
    cro_mention = _mention("cro", "CRO")
    await post_message(
        client,
        VERDICT_ROOM_ID,
        PHASE3_TRIGGER_TEMPLATE.format(user=BAND_USER),
        mentions=[cro_mention] if cro_mention else [],
    )


async def _phase3_loop(client: httpx.AsyncClient) -> bool:
    """Watch Verdict room for the final CRO output."""
    messages = await fetch_messages(client, VERDICT_ROOM_ID)
    for m in reversed(messages):
        content = _content(m)
        if PHASE3_MARKER in content:
            return True
    return False


async def orchestrate() -> None:
    _require_env()
    mode = "SINGLE-ROOM" if SINGLE_ROOM_MODE else "3-ROOM BREAKOUT"
    log.info("🎬 GreenLight orchestrator — %s mode", mode)
    log.info("    briefing:   %s", BRIEFING_ROOM_ID)
    log.info("    cross-exam: %s", CROSS_EXAM_ROOM_ID)
    log.info("    verdict:    %s", VERDICT_ROOM_ID)
    log.info("    poll: %ds | phase1 timeout: %ds", POLL_INTERVAL_SECS, PHASE1_TIMEOUT_SECS)

    state = PhaseState()
    phase = 1
    cross_exam_summary: str | None = None

    async with httpx.AsyncClient() as client:
        while True:
            try:
                if phase == 1:
                    done = await _phase1_loop(client, state)
                    if done:
                        log.info("🔴 Phase 1 complete — forwarding to Cross-Examination")
                        await _forward_reports_to_cross_exam(client, state)
                        phase = 2

                elif phase == 2:
                    summary = await _phase2_loop(client)
                    if summary:
                        cross_exam_summary = summary
                        log.info("🟡 Phase 2 complete — forwarding to Verdict")
                        await _forward_to_verdict(client, state, cross_exam_summary)
                        phase = 3

                elif phase == 3:
                    if await _phase3_loop(client):
                        log.info("🟢 Phase 3 complete — verdict delivered. Done.")
                        return

            except httpx.HTTPError as exc:
                log.warning("Band API error (will retry): %s", exc)
            except Exception as exc:  # noqa: BLE001 — keep loop alive
                log.exception("Orchestrator error: %s", exc)

            await asyncio.sleep(POLL_INTERVAL_SECS)


if __name__ == "__main__":
    asyncio.run(orchestrate())
