"""
Upload page — collect a film project package, build the kickoff message,
and copy it to the user's clipboard for pasting into the Band room.

Why clipboard instead of direct POST?
  Band's human chat-write API requires a tier our user key doesn't have
  (returns 403 "Agent authentication not allowed"). The agents themselves
  use a different API path that works. So the cleanest flow is:
    1. User builds the package here
    2. We copy the formatted kickoff to clipboard
    3. User pastes into the Band UI manually
    4. Agents pick it up and run via their @-mention routing
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from band_client import copy_to_clipboard

st.set_page_config(page_title="GreenLight — Upload", page_icon="📤", layout="wide")
st.title("📤 Upload a film project")
st.caption(
    "Provide as much as you have. Missing pieces are flagged by the agents — "
    "not fabricated."
)

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


def _read_uploaded(file) -> str:
    """Return the text content of an uploaded file (txt/md/csv/json/pdf)."""
    if file is None:
        return ""
    name = file.name.lower()
    raw = file.read()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return "\n\n".join((p.extract_text() or "") for p in reader.pages).strip()
        except Exception as exc:  # noqa: BLE001
            return f"(PDF parse error: {exc})"
    if name.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(raw))
            return df.to_csv(index=False)
        except Exception:
            pass
    return raw.decode("utf-8", errors="replace")


col_l, col_r = st.columns(2)

with col_l:
    st.subheader("🎬 Script / treatment")
    script_file = st.file_uploader(
        "Upload .pdf / .txt / .md", type=["pdf", "txt", "md"], key="script_file"
    )
    script_text = st.text_area(
        "...or paste the screenplay text",
        value=st.session_state.get("script_text", ""),
        height=240,
    )
    if script_file is not None:
        script_text = _read_uploaded(script_file)

    st.subheader("👥 Crew list")
    crew_file = st.file_uploader(
        "Upload .json / .txt", type=["json", "txt"], key="crew_file"
    )
    crew_text = st.text_area(
        "...or paste the crew JSON",
        value=st.session_state.get("crew_text", ""),
        height=160,
    )
    if crew_file is not None:
        crew_text = _read_uploaded(crew_file)

with col_r:
    st.subheader("💰 Production budget")
    budget_file = st.file_uploader(
        "Upload .csv / .xlsx / .pdf / .txt",
        type=["csv", "xlsx", "pdf", "txt"],
        key="budget_file",
    )
    budget_text = st.text_area(
        "...or paste the budget CSV",
        value=st.session_state.get("budget_text", ""),
        height=240,
    )
    if budget_file is not None:
        budget_text = _read_uploaded(budget_file)

    st.subheader("⚖️ Contracts / deal memos (optional)")
    legal_file = st.file_uploader(
        "Upload .pdf / .txt", type=["pdf", "txt"], key="legal_file"
    )
    legal_text = st.text_area(
        "...or paste deal memos",
        value=st.session_state.get("legal_text", ""),
        height=160,
    )
    if legal_file is not None:
        legal_text = _read_uploaded(legal_file)


def _build_kickoff_message() -> str:
    parts: list[str] = [
        "@ScriptAnalyst @BudgetAuditor @MarketIntel @LegalEagle @TalentScout "
        "please analyze this film project package:",
        "",
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
    return "\n".join(parts)


st.markdown("---")
left, right = st.columns([1, 3])
with left:
    submit = st.button(
        "📋 Copy kickoff to clipboard",
        type="primary",
        use_container_width=True,
    )
with right:
    st.caption(
        "Builds the kickoff message and copies it to your clipboard. "
        "Paste it into the Band Briefing room — the agents will pick it up "
        "and chain through Phase 1 → 2 → 3 automatically via @mention routing."
    )

if submit:
    if not project_title:
        st.error("Project title is required.")
        st.stop()
    if not script_text and not budget_text and not crew_text:
        st.error("Provide at least one document (script, budget, or crew list).")
        st.stop()

    if crew_text.strip().startswith("{"):
        try:
            json.loads(crew_text)
        except json.JSONDecodeError as exc:
            st.warning(f"Crew JSON failed to parse but will be sent anyway: {exc}")

    message = _build_kickoff_message()

    if copy_to_clipboard(message):
        st.success(
            f"✅ Kickoff copied to clipboard ({len(message):,} chars). "
            "Switch to the Band room and **paste (Ctrl+V) → Send**."
        )
        st.balloons()
    else:
        st.warning(
            "Clipboard copy failed (no clipboard helper found). "
            "Copy the text below manually."
        )

    with st.expander("📝 Or copy the kickoff text manually", expanded=False):
        st.code(message, language="markdown")
