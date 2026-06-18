# 🎬 GreenLight AI

> **The AI investment committee that never sleeps.**
> 7 specialized agents · 4 framework adapters · 3 LLM providers · 1 Band room.

GreenLight AI is a multi-agent due diligence system for film investors. A
producer uploads a project package (script, budget, crew, deal memos) and a
team of seven AI agents collaboratively analyzes it through a Band chat room
— auditing script complexity, budget adequacy, market viability, legal
exposure, and team track record — before a Red Team agent cross-examines
the findings and a Chief Risk Officer delivers a final investment verdict.

Built for the [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon)
(Track 3 — Regulated & High-Stakes Workflows).

---

## Architecture — phase-isolated breakout rooms

```
ROOM 1 — Briefing                ROOM 2 — Cross-Examination       ROOM 3 — Verdict
─────────────────────            ─────────────────────────        ────────────────
You + 5 specialists       ──▶    You + RedTeam + 5 specialists   ──▶    You + CRO

@ScriptAnalyst, @BudgetAuditor,  Orchestrator forwards the 5     Orchestrator forwards
@MarketIntel, @LegalEagle,       reports cleanly. RedTeam runs   reports + RedTeam
@TalentScout deliver structured  cross-examination, issues       summary. CRO produces
Phase 1 reports.                 challenges (C-1..C-N), tracks   the final scorecard +
                                 resolutions, posts summary.     verdict.
```

Each phase room only sees what it needs. The orchestrator
(`orchestrator/workflow.py`) watches Room 1 for completion markers,
captures each specialist's report, and forwards them as clean messages
into Room 2 — and similarly Room 2 → Room 3. Full architecture details
in [docs/breakout_rooms.md](docs/breakout_rooms.md).

**Single-room fallback:** if you leave the breakout room IDs unset, the
system runs all 7 agents in the legacy single room (good for quick
tests).

### Agent ↔ framework ↔ provider matrix

| Agent | Framework adapter | Provider (demo mode) | Model |
|-------|------------------|----------------------|-------|
| @ScriptAnalyst | Google ADK | Gemini (free) | gemini-2.5-flash |
| @BudgetAuditor | LangGraph | Groq (free) | llama-3.3-70b-versatile |
| @MarketIntel | Google ADK | Gemini (free) | gemini-2.5-flash |
| @LegalEagle | LangGraph | Featherless (trial) | Llama-3.3-70B-Instruct |
| @TalentScout | LangGraph | Groq (free) | qwen/qwen3-32b |
| @RedTeam | Google ADK | Gemini (free) | gemini-2.5-flash |
| @CRO | CrewAI | Featherless (trial) | DeepSeek-R1-Distill-Llama-70B |

In **dev mode** (`LLM_MODE=dev`) every agent routes through Gemini so the
Featherless trial token budget is preserved for demo recording.

---

## Repository layout

```
greenlight-ai/
├── agents/                 # one Python file per agent + llm_router.py
├── prompts/                # v2 system prompts (XML-structured, evidence-cited)
├── orchestrator/           # phase-transition controller
├── frontend/               # Streamlit dashboard (Upload, Debate, Scorecard)
├── demo_data/              # "The Deep Horizon" sample project
├── config/                 # agent_config.yaml.example
├── docs/                   # architecture + pitch deck outline
├── run_all_agents.py       # launcher for all 7 agent processes
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Quick start

### 0. Prerequisites
- Python 3.10+
- A [Band](https://app.band.ai) account
- Free API keys: [Gemini](https://aistudio.google.com/app/apikey), [Groq](https://console.groq.com/keys)
- Featherless trial key with promo `BOA26` (for partner-prize eligibility)

### 1. Install
```bash
git clone <this-repo>
cd greenlight-ai
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Register Band agents
For each of the 7 agents, on https://app.band.ai/agents:
1. Click **New Agent → External Agent**
2. Name it exactly as listed in the matrix above (`ScriptAnalyst`, etc.)
3. Copy the UUID and API key (the key is shown only once)

Then copy the template and fill in the values:
```bash
cp config/agent_config.yaml.example config/agent_config.yaml
# edit config/agent_config.yaml
```

### 3. Add env vars
```bash
cp .env.example .env
# edit .env with your LLM provider keys and Band room ID
```

### 4. Run the agents
```bash
python run_all_agents.py
```

All seven agent processes start. Each connects to Band via WebSocket and
listens for messages where it is @mentioned.

### 5. Launch the frontend
In a second terminal:
```bash
streamlit run frontend/app.py
```

Then open the URL Streamlit prints. Use the **Upload** page to submit the
sample project, **Debate** to watch the agents work, and **Scorecard** for
the final verdict.

### 6. Run the orchestrator (optional)
```bash
python -m orchestrator.workflow
```

The orchestrator polls the Band room, detects when each phase finishes, and
posts the trigger for the next phase. Without it, you can drive the phase
transitions manually from the Band UI.

---

## Demo data

`demo_data/` contains **"The Deep Horizon"** — a $7.26M sci-fi thriller with
seven deliberate red flags planted across the package. The agents should find:

1. Marine unit is budgeted at $0 but the script requires extensive underwater work
2. Aerial unit is budgeted at $0 but Act 3 needs helicopter shots
3. E&O insurance is $0 (mandatory for distribution)
4. Completion bond is $0 (typically required for budgets > $2M)
5. VFX budget is ~$46K/shot vs $80–150K industry minimum for water/CG work
6. Contingency is 4.1% vs 10% industry standard
7. No A-list cast attached, but market projections may assume star-driven comps

If the demo is working, **@RedTeam** will surface the VFX shortfall by
comparing **@ScriptAnalyst**'s shot count against **@BudgetAuditor**'s
per-shot figure. That cross-agent insight is the killer finding — no single
agent could produce it.

---

## Tech stack

- **[Band](https://band.ai)** — chat-room coordination, @mention routing,
  audit trail
- **[band-sdk](https://docs.band.ai)** — multi-framework adapter layer
  (Anthropic, LangGraph, CrewAI, PydanticAI, Google ADK)
- **[Streamlit](https://streamlit.io)** — frontend dashboard
- **[Plotly](https://plotly.com)** — radar chart on the scorecard

---

## Hackathon submission checklist

- [x] Public GitHub repository
- [x] At least 3 agents collaborating through Band ✅ (we have 7)
- [x] Cross-framework demonstration ✅ (4 adapters)
- [x] Multi-provider demonstration ✅ (3 providers)
- [ ] Cover image (TODO: add to `frontend/assets/`)
- [ ] Demo video (script in `docs/demo_script.md`)
- [ ] Pitch deck (outline in `docs/pitch_deck.md`)
- [ ] Live demo URL (deploy `streamlit run frontend/app.py` to Streamlit Cloud)

---

## Credits

Built for the Band of Agents Hackathon, June 2026.
Prompt design draws on research from MetaGPT, PROCLAIM, DebateCV,
AgenticSimLaw, and Anthropic's published best practices.

## License

MIT. See `LICENSE`.

## Disclaimer

GreenLight AI is a decision-support tool. It does not constitute financial
or legal advice. Human judgment is essential for all investment decisions.
