"""
Scorecard page — render the CRO's final risk scorecard.

Pulls the latest CRO message from the Band room, extracts component scores via
light regex, and renders a radar chart + summary table. Falls back to showing
the raw CRO markdown if parsing fails.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import plotly.graph_objects as go
import streamlit as st

from band_client import fetch_messages

st.set_page_config(page_title="GreenLight — Scorecard", page_icon="🎬", layout="wide")
st.title("🎬 Investment risk scorecard")


@dataclass
class Scorecard:
    project: str | None
    summary: str | None
    verdict: str | None
    overall: int | None
    components: dict[str, int]
    raw: str


COMPONENT_LABELS = {
    "Script Feasibility":  "ScriptAnalyst",
    "Budget Adequacy":     "BudgetAuditor",
    "Market Viability":    "MarketIntel",
    "Legal Compliance":    "LegalEagle",
    "Talent & Team":       "TalentScout",
}


def _latest_cro_message(messages: list[dict]) -> str | None:
    for m in reversed(messages):
        sender = (m.get("sender_name") or m.get("sender") or "").lstrip("@")
        content = m.get("content") or ""
        if sender == "CRO" and "VERDICT" in content:
            return content
    return None


def _parse(raw: str) -> Scorecard:
    project = None
    m = re.search(r"### Project:\s*(.+)", raw)
    if m:
        project = m.group(1).strip()

    overall = None
    m = re.search(r"OVERALL RISK SCORE[:\s]+(\d+)", raw, re.IGNORECASE)
    if m:
        try:
            overall = int(m.group(1))
        except ValueError:
            overall = None

    verdict = None
    m = re.search(r"VERDICT[:\s*]+([🟢🟡🔴]+\s*\w+)", raw)
    if m:
        verdict = m.group(1).strip()

    # Components — try to find the post-revision number per row.
    components: dict[str, int] = {}
    for label in COMPONENT_LABELS:
        pat = rf"{re.escape(label)}.*?(\d+)\s*/\s*10.*?(\d+)\s*/\s*10"
        m = re.search(pat, raw, re.DOTALL)
        if m:
            components[label] = int(m.group(2))
            continue
        pat = rf"{re.escape(label)}.*?(\d+)\s*/\s*10"
        m = re.search(pat, raw, re.DOTALL)
        if m:
            components[label] = int(m.group(1))

    summary = None
    m = re.search(r"EXECUTIVE SUMMARY\s*\n+(.+?)\n\s*---", raw, re.DOTALL)
    if m:
        summary = m.group(1).strip()

    return Scorecard(project, summary, verdict, overall, components, raw)


def _verdict_color(text: str | None) -> str:
    if not text:
        return "#888"
    if "GREENLIGHT" in text or "🟢" in text:
        return "#00d97e"
    if "CONDITIONAL" in text or "🟡" in text:
        return "#f7c948"
    if "PASS" in text or "🔴" in text:
        return "#ef4444"
    return "#888"


# ----- main -----
try:
    messages = fetch_messages(phase="verdict")
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load messages from Band: {exc}")
    st.stop()

raw = _latest_cro_message(messages)
if not raw:
    st.info(
        "No CRO scorecard found yet. "
        "Once Phase 3 completes, the verdict will appear here automatically."
    )
    st.stop()

sc = _parse(raw)

# ---- header strip ----
hl, hr = st.columns([3, 2])
with hl:
    if sc.project:
        st.subheader(sc.project)
    if sc.summary:
        st.write(sc.summary)
with hr:
    color = _verdict_color(sc.verdict)
    st.markdown(
        f"""
        <div style="background: {color}22; border: 2px solid {color};
                    border-radius: 12px; padding: 24px; text-align: center;">
            <div style="color: #b3b9c5; font-size: 14px;">VERDICT</div>
            <div style="color: {color}; font-size: 36px; font-weight: 800;
                        margin: 8px 0;">{sc.verdict or 'PENDING'}</div>
            <div style="color: #b3b9c5; font-size: 14px;">
                {f"Score: {sc.overall}/100" if sc.overall is not None else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---- radar + table ----
left, right = st.columns([3, 2])
with left:
    if sc.components:
        labels = list(sc.components.keys())
        values = [sc.components[l] for l in labels]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            line=dict(color="#00d97e", width=2),
            fillcolor="rgba(0, 217, 126, 0.25)",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d8dce6"),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Component scores not yet parseable — see raw report below.")

with right:
    st.subheader("Component scores")
    if sc.components:
        for label, score in sc.components.items():
            agent = COMPONENT_LABELS[label]
            st.markdown(
                f"**{label}** &nbsp;·&nbsp; "
                f"<span style='color:#888'>@{agent}</span> &nbsp;·&nbsp; "
                f"<span style='color:#00d97e; font-weight:700'>{score}/10</span>",
                unsafe_allow_html=True,
            )
            st.progress(score / 10)
    else:
        st.caption("Awaiting parseable scorecard.")

st.markdown("---")
with st.expander("📄 View raw CRO report"):
    st.markdown(raw)
