"""
GreenLight AI — Streamlit dashboard entry point.

Pages:
    Upload    — submit a film project package and trigger Phase 1
    Debate    — live view of the Band room conversation
    Scorecard — render the CRO's final risk scorecard

Streamlit auto-discovers files in pages/ and shows them in the sidebar.
This file is the home/landing screen.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="GreenLight AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(135deg, #0e1117 0%, #1a1d29 100%);
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #2a2f3e;
        margin-bottom: 24px;
    }
    .hero h1 { color: #00d97e; margin: 0 0 8px 0; font-size: 42px; }
    .hero p  { color: #b3b9c5; font-size: 18px; margin: 0; }
    .stat-card {
        background: #1a1d29;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #00d97e;
    }
    .stat-card .value { color: #00d97e; font-size: 32px; font-weight: 700; }
    .stat-card .label { color: #b3b9c5; font-size: 14px; }
    </style>

    <div class="hero">
        <h1>🎬 GreenLight AI</h1>
        <p>The AI investment committee that never sleeps. Seven specialized agents.
        Four frameworks. Three providers. One Band room.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        '<div class="stat-card"><div class="value">7</div>'
        '<div class="label">Specialist Agents</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="stat-card"><div class="value">3</div>'
        '<div class="label">Analysis Phases</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="stat-card"><div class="value">4</div>'
        '<div class="label">Framework Adapters</div></div>',
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        '<div class="stat-card"><div class="value">~5min</div>'
        '<div class="label">End-to-end Analysis</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

left, right = st.columns([3, 2])
with left:
    st.subheader("How it works")
    st.markdown(
        """
        **Phase 1 — Parallel analysis.** Five specialists work simultaneously in a
        Band chat room:

        - **@ScriptAnalyst** breaks down production complexity, VFX counts, locations, shoot days
        - **@BudgetAuditor** audits the budget for red flags and cross-references against script requirements
        - **@MarketIntel** pulls comparable films and projects ROI
        - **@LegalEagle** checks chain of title, guild compliance, and required protections
        - **@TalentScout** scores the team's track record and execution risk

        **Phase 2 — Adversarial cross-examination.** **@RedTeam** reads every report,
        finds contradictions across agents, and issues formal challenges. Challenged
        agents defend or revise. This is where the killer findings live.

        **Phase 3 — Verdict.** **@CRO** synthesizes everything (using post-revision
        scores) into a weighted scorecard and a clear **GREENLIGHT / CONDITIONAL / PASS**
        verdict with specific conditions.
        """
    )
with right:
    st.subheader("Get started")
    st.info("Use the sidebar to navigate.\n\n"
            "1. **Upload** a project package\n"
            "2. **Debate** view to watch the agents argue\n"
            "3. **Scorecard** for the final verdict")
    st.caption(
        "Built for the **Band of Agents Hackathon** on lablab.ai. "
        "Track 3 — Regulated & High-Stakes Workflows."
    )

st.markdown("---")
st.caption(
    "GreenLight AI is a decision-support tool. It does not constitute "
    "financial or legal advice. Human judgment is essential for all investment decisions."
)
