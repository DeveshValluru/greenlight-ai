"""
Debate page — live, auto-refreshing view of the Band room conversation.

This is the hero screen for the demo. Each agent gets its own color so the
adversarial back-and-forth between RedTeam and the specialists reads at a
glance.
"""
from __future__ import annotations

import html
import time

import streamlit as st

from band_client import fetch_messages

st.set_page_config(page_title="GreenLight — Debate", page_icon="🔴", layout="wide")
st.title("🔴 Live debate — Band room")
st.caption("Real-time view of the 7-agent investment committee.")

# ----- agent color palette -----
AGENT_COLORS: dict[str, str] = {
    "ScriptAnalyst":   "#4A90D9",
    "BudgetAuditor":   "#D94A4A",
    "MarketIntel":     "#4AD97A",
    "LegalEagle":      "#D9C84A",
    "TalentScout":     "#9B4AD9",
    "RedTeam":         "#FF4444",
    "CRO":             "#FFD700",
    "SpecialistOnCall": "#4ADBD9",
}
DEFAULT_COLOR = "#888"


def _phase(all_text: str) -> tuple[int, str]:
    if "VERDICT:" in all_text:
        return 3, "🟢 Phase 3 — Verdict delivered"
    if "CROSS-EXAMINATION SUMMARY" in all_text:
        return 2, "🔴 Phase 2 — Cross-examination complete"
    if any(m in all_text for m in [
        "FEASIBILITY SCORE", "BUDGET ADEQUACY SCORE",
        "COMMERCIAL VIABILITY SCORE", "LEGAL RISK SCORE", "TALENT RISK SCORE",
    ]):
        return 1, "🔵 Phase 1 — Specialists reporting"
    return 0, "⚪ Awaiting kickoff"


def _render_message(msg: dict) -> None:
    sender = msg.get("sender_name") or msg.get("sender") or "Unknown"
    sender_key = sender.lstrip("@")
    content = msg.get("content") or msg.get("text") or ""
    color = AGENT_COLORS.get(sender_key, DEFAULT_COLOR)

    safe_content = html.escape(content).replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="border-left: 4px solid {color}; padding: 10px 14px;
                    margin: 10px 0; background: rgba(255,255,255,0.02);
                    border-radius: 6px;">
            <div style="color: {color}; font-weight: 700; font-size: 14px;
                        margin-bottom: 6px;">@{html.escape(sender_key)}</div>
            <div style="color: #d8dce6; font-size: 14px; line-height: 1.5;">
                {safe_content}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----- controls -----
top_l, top_r = st.columns([3, 1])
with top_r:
    auto = st.toggle("Auto-refresh (3s)", value=True)
    if st.button("🔄 Refresh now"):
        st.rerun()

# ----- main feed -----
try:
    messages = fetch_messages()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load messages from Band: {exc}")
    st.stop()

all_text = " ".join((m.get("content") or "") for m in messages)
phase_num, phase_label = _phase(all_text)

with top_l:
    st.header(phase_label)
    if phase_num == 1:
        completed = [
            n for n, m in {
                "ScriptAnalyst":  "FEASIBILITY SCORE",
                "BudgetAuditor":  "BUDGET ADEQUACY SCORE",
                "MarketIntel":    "COMMERCIAL VIABILITY SCORE",
                "LegalEagle":     "LEGAL RISK SCORE",
                "TalentScout":    "TALENT RISK SCORE",
            }.items() if m in all_text
        ]
        st.progress(len(completed) / 5, text=f"{len(completed)}/5 specialist reports posted")

st.markdown("---")
if not messages:
    st.info("No messages yet. Use the Upload page to kick off an analysis.")
else:
    for m in messages:
        _render_message(m)

if auto:
    time.sleep(3)
    st.rerun()
