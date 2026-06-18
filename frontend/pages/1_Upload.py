"""
Upload page — collect a film project package and kick off Phase 1.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from band_client import post_message

st.set_page_config(page_title="GreenLight — Upload", page_icon="📤", layout="wide")
st.title("📤 Upload a film project")
st.caption("Provide as much as you have. Missing pieces are flagged by the agents — not fabricated.")

DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "demo_data"

with st.expander("💡 Use the sample project (recommended for first run)"):
    if st.button("Load 'The Deep Horizon' demo data"):
        st.session_state["project_title"] = "The Deep Horizon"
        st.session_state["script_text"] = (DEMO_DIR / "sample_script.txt").read_text(encoding="utf-8")
        st.session_state["budget_text"] = (DEMO_DIR / "sample_budget.csv").read_text(encoding="utf-8")
        st.session_state["crew_text"]   = (DEMO_DIR / "sample_crew.json").read_text(encoding="utf-8")
        st.session_state["legal_text"]  = (DEMO_DIR / "sample_contracts.txt").read_text(encoding="utf-8")
        st.success("Sample project loaded into the form below.")


project_title = st.text_input(
    "Project title",
    value=st.session_state.get("project_title", ""),
    placeholder="e.g. The Deep Horizon",
)

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("🎬 Script / treatment")
    script_file = st.file_uploader("Upload .txt / .md", type=["txt", "md"], key="script_file")
    script_text = st.text_area(
        "...or paste the screenplay text",
        value=st.session_state.get("script_text", ""),
        height=240,
    )
    if script_file is not None:
        script_text = script_file.read().decode("utf-8", errors="replace")

    st.subheader("👥 Crew list")
    crew_file = st.file_uploader("Upload .json / .txt", type=["json", "txt"], key="crew_file")
    crew_text = st.text_area(
        "...or paste the crew JSON",
        value=st.session_state.get("crew_text", ""),
        height=160,
    )
    if crew_file is not None:
        crew_text = crew_file.read().decode("utf-8", errors="replace")

with col_r:
    st.subheader("💰 Production budget")
    budget_file = st.file_uploader("Upload .csv / .txt", type=["csv", "txt"], key="budget_file")
    budget_text = st.text_area(
        "...or paste the budget CSV",
        value=st.session_state.get("budget_text", ""),
        height=240,
    )
    if budget_file is not None:
        raw = budget_file.read()
        try:
            df = pd.read_csv(io.BytesIO(raw))
            budget_text = df.to_csv(index=False)
        except Exception:
            budget_text = raw.decode("utf-8", errors="replace")

    st.subheader("⚖️ Contracts / deal memos (optional)")
    legal_file = st.file_uploader("Upload .txt", type=["txt"], key="legal_file")
    legal_text = st.text_area(
        "...or paste deal memos",
        value=st.session_state.get("legal_text", ""),
        height=160,
    )
    if legal_file is not None:
        legal_text = legal_file.read().decode("utf-8", errors="replace")


def _build_kickoff_message() -> str:
    parts: list[str] = [
        "=== GREENLIGHT AI — PROJECT ANALYSIS REQUEST ===",
        f"PROJECT: {project_title or '(untitled)'}",
        "",
        "--- SCRIPT / TREATMENT ---",
        script_text or "(NOT PROVIDED)",
        "",
        "--- BUDGET ---",
        budget_text or "(NOT PROVIDED)",
        "",
        "--- CREW LIST ---",
        crew_text or "(NOT PROVIDED)",
    ]
    if legal_text:
        parts += ["", "--- LEGAL DOCS ---", legal_text]
    parts += [
        "",
        "--- END OF PROJECT DOCUMENTS ---",
        "",
        "@Devesh Valluru/scriptanalyst @Devesh Valluru/budgetauditor @Devesh Valluru/marketintel "
        "@Devesh Valluru/legaleagle @Devesh Valluru/talentscout",
        "Please analyze this project and post your reports following the standard format.",
    ]
    return "\n".join(parts)


st.markdown("---")
left, right = st.columns([1, 3])
with left:
    submit = st.button("🚀 Run GreenLight Analysis", type="primary", use_container_width=True)
with right:
    st.caption(
        "On submit, the project package is posted to the Band room and the five "
        "Phase 1 specialists are @mentioned in parallel. The orchestrator will "
        "trigger Phase 2 and 3 automatically once each phase completes."
    )

if submit:
    if not project_title:
        st.error("Project title is required.")
        st.stop()
    if not script_text and not budget_text and not crew_text:
        st.error("Provide at least one document (script, budget, or crew list).")
        st.stop()

    # Quick sanity-check JSON-ish crew input so the agents don't waste a turn on
    # a parse error. The agents are tolerant of free-form text too.
    if crew_text.strip().startswith("{"):
        try:
            json.loads(crew_text)
        except json.JSONDecodeError as exc:
            st.warning(f"Crew JSON failed to parse but will be sent anyway: {exc}")

    message = _build_kickoff_message()
    try:
        post_message(message)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Failed to post to Band room: {exc}")
        st.stop()

    st.success("Analysis kicked off! Switch to the Debate page to watch the agents work.")
    st.balloons()
