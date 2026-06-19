# 🎬 GreenLight AI

> **The AI investment committee that never sleeps.**
> 7 specialized agents · 3 framework adapters · 3 model tiers · 1 Band room.

GreenLight AI is a multi-agent due-diligence system for film investors. A
producer pastes a project package (script, budget, crew, deal memos) into a
Band chat room. Seven specialized AI agents then collaboratively analyze it
through **agent-to-agent @mention routing** — auditing script complexity,
budget adequacy, market viability, legal exposure, and team track record —
before a Red Team agent cross-examines the findings and a Chief Risk Officer
delivers a final investment verdict.

Built for the [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon)
(Track 3 — Regulated & High-Stakes Workflows).

---

## Architecture — chat-as-protocol

GreenLight uses Band's `@mention` routing as its native coordination protocol.
There is **no central orchestrator**. Each agent's prompt ends with a handoff
@mention to the next phase, so the chain self-propagates through Band:

```
Human posts kickoff (@-mentions 5 specialists)
   │
   ▼
Phase 1 — 5 specialists analyze in parallel
   • @ScriptAnalyst      complexity, VFX, locations, shoot days
   • @BudgetAuditor      cross-reference VFX/locations/days vs budget
   • @MarketIntel        comparable films + revenue projections
   • @LegalEagle         IP, guild, insurance, completion bond
   • @TalentScout        track record + execution risk
   │
   │  Each specialist ends its report with: "@RedTeam ready for cross-examination."
   ▼
Phase 2 — @RedTeam adversarial cross-examination
   • Reads all 5 reports
   • Issues 3–7 formal CHALLENGE [C-N] entries
   • Tracks RESOLVED / PARTIAL / UNRESOLVED
   • Ends with: "@CRO ready for final scorecard."
   ▼
Phase 3 — @CRO synthesis
   • Weighted scorecard (Budget 25%, Market 25%, Script 20%, Legal 15%, Talent 15%)
   • Verdict: 🟢 GREENLIGHT (70+) / 🟡 CONDITIONAL (40–69) / 🔴 PASS (<40)
   • Top 5 risks + conditions for approval
```

Every message — analysis, challenge, defense, revision, verdict — lives in
the same Band room. **The chat history IS the audit trail.**

### Agent ↔ framework ↔ model matrix

Each agent uses a different framework adapter and a Gemini model tier
matched to its workload:

| Agent | Framework | Model | Tier | Workload |
|-------|-----------|-------|------|----------|
| **@ScriptAnalyst** | Google ADK | gemini-2.5-flash | standard | parse + structure a screenplay |
| **@BudgetAuditor** | LangGraph | gemini-2.5-flash | standard | numeric cross-reference across reports |
| **@MarketIntel** | Google ADK | gemini-2.5-flash-lite | lite | lookup comparable films |
| **@LegalEagle** | LangGraph | gemini-2.5-flash | standard | legal/compliance reasoning |
| **@TalentScout** | LangGraph | gemini-2.5-flash-lite | lite | personnel evaluation |
| **@RedTeam** | Google ADK | gemini-2.5-flash | standard | adversarial reasoning across 5 reports |
| **@CRO** | CrewAI | gemini-2.5-flash | standard | weighted-score synthesis + verdict |

**3 framework adapters · 1 provider · 2 active model tiers** running
together through Band's protocol. The routing logic lives in
[agents/llm_router.py](agents/llm_router.py) and the configuration also
includes a `gemini-2.5-pro` "heavy" tier ready to swap in for any agent.

The standard tier (`gemini-2.5-flash`) was chosen over Pro for the demo
because Pro's free-tier daily request cap is 50 — the seven-agent debate
exhausts that within 1-2 demo runs. Flash has 1,500 daily requests, which
lets the demo run many times during recording without hitting 429s.

### How the agents coordinate

There's **no central orchestrator** for the default demo. Each agent's
system prompt contains:

- **`<mandatory_initial_output>`** — every specialist MUST produce a
  primary report on first invocation, even if dependencies (other agents'
  reports) aren't yet available. Cross-reference sections mark
  `PENDING — will update when @SourceAgent posts` rather than blocking.
- **`<closing_handoff>`** — each specialist ends its report with
  `@RedTeam my report is complete and ready for your cross-examination.`
  RedTeam ends its summary with `@CRO ready for verdict`. The chain
  self-propagates through Band's `@mention` router.
- **`<response_discipline>`** — agents respond ONLY when asked a direct
  question or assigned a task. Citations and references in other agents'
  messages do NOT trigger a reply.
- **`<no_ack_messages>`** — absolute ban on content-free messages
  (`Acknowledged`, `Standing by`, `Confirmed`, `Thank you`). If an agent
  has nothing substantive to add, it stays silent. This blocks the
  infinite acknowledgment loops that emerge naturally when agents
  reference each other.

These four prompt blocks are what make a pure mention-routed system stable.
Without them, agents either stall waiting for peers, never trigger the
next phase, or chat-spam each other with social closures.

---

## Repository layout

```
greenlight-ai/
├── agents/                 # one Python file per agent + llm_router.py
├── prompts/                # v2 XML-structured prompts with handoff blocks
├── frontend/               # Streamlit (Upload + Debate + Scorecard)
├── demo_data/              # "The Deep Horizon" sample project + build helper
├── config/                 # agent_config.yaml.example
├── orchestrator/           # EXPERIMENTAL polling orchestrator (paid Band tier)
├── docs/                   # architecture notes, pitch deck, demo script
├── run_all_agents.py       # launches all 7 agent processes
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Quick start

### 0. Prerequisites
- Python 3.10+
- A [Band](https://app.band.ai) account
- A free [Gemini](https://aistudio.google.com/app/apikey) API key (only key needed)

### 1. Install
```bash
git clone https://github.com/DeveshValluru/greenlight-ai.git
cd greenlight-ai
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

If `pip install` hits `resolution-too-deep`, install in batches — see
[docs/HANDOFF.md §11.6](docs/HANDOFF.md).

### 2. Register agents on Band
For each of the 7 agents at https://app.band.ai/agents:
1. Click **New Agent → External Agent**
2. Name it `ScriptAnalyst`, `BudgetAuditor`, `MarketIntel`, `LegalEagle`,
   `TalentScout`, `RedTeam`, `CRO` (exactly these names — they're the
   @mention handles)
3. Copy the **agent UUID** and **API key** (key shown only once)

Then:
```bash
cp config/agent_config.yaml.example config/agent_config.yaml
# fill in the UUIDs and API keys
```

### 3. Set up environment variables
```bash
cp .env.example .env
# edit .env — minimum required: GOOGLE_API_KEY and GREENLIGHT_ROOM_ID
```

### 4. Create a Band chat room
- Create one chat room in Band UI
- Add all 7 agents as participants
- Copy the room UUID into `.env` as `GREENLIGHT_ROOM_ID`

### 5. Run the agents
```bash
python run_all_agents.py
```

Seven processes spin up — each connects to Band via WebSocket and listens
for messages where it is @-mentioned.

### 6. Launch the Streamlit frontend (optional)
```bash
streamlit run frontend/app.py
```

The Streamlit UI is a convenience wrapper:
- **Upload** — drag in your script / budget / crew, click "Copy kickoff to
  clipboard", paste into the Band room
- **Debate** — live read of the room conversation (uses an agent's API key)
- **Scorecard** — parses the CRO's final scorecard into a radar chart

You can skip Streamlit entirely and drive the demo from the Band chat UI.

### 7. Kick it off
In the Band chat room, paste the kickoff (or your own project) starting
with `@ScriptAnalyst @BudgetAuditor @MarketIntel @LegalEagle @TalentScout`
and the project data below it. Within ~2 minutes you'll see all 5 reports,
then RedTeam's cross-examination, then CRO's verdict — all driven by the
agents @mentioning each other.

---

## "The Deep Horizon" demo data

[demo_data/](demo_data) contains a $7.26M sci-fi-thriller package with
seven planted red flags. The agents should find:

1. **Marine unit is budgeted at $0** but the script needs underwater filming
2. **Aerial unit is budgeted at $0** but Act 3 needs helicopter shots
3. **E&O insurance is $0** — mandatory for distribution
4. **Completion bond is $0** — required for budgets > $2M
5. **VFX is $46K/shot vs $80–150K** industry minimum for water/CG work
6. **Contingency is 4.1% vs 10%** industry standard
7. **No A-list cast** attached, but market projections may assume star power

If the system is working, **@RedTeam surfaces the ~$1.5M VFX shortfall by
comparing @ScriptAnalyst's shot count against @BudgetAuditor's per-shot
figure**. That cross-agent insight is the killer finding — no single agent
could have produced it.

To build a kickoff message from any mix of PDFs / CSVs / JSONs / TXT files:
```bash
python demo_data/build_kickoff.py --script my_script.pdf --budget my_budget.csv
```

The message is built and copied to your clipboard. Paste into Band, send.

---

## Tech stack

- **[Band](https://band.ai)** — chat-room coordination, @mention routing,
  agent registration, audit trail
- **[band-sdk](https://docs.band.ai)** — Python SDK with framework adapters
  (Google ADK, LangGraph, CrewAI, PydanticAI, Anthropic — we use 3)
- **[Streamlit](https://streamlit.io)** — frontend wrapper
- **[Plotly](https://plotly.com)** — radar chart on the scorecard

---

## What about the orchestrator?

[orchestrator/workflow.py](orchestrator/workflow.py) is an **experimental**
polling orchestrator that watches each phase room and forwards artifacts
between phases. It requires write access to Band's `/api/v1/me/chats/...`
endpoint, which a paid Band tier exposes but the free tier does not.

**The default demo does not use the orchestrator.** Agent-to-agent @mention
handoff (configured in [prompts/](prompts)) makes it unnecessary. We've left
the orchestrator in the repo as a reference for production deployments on
paid Band tiers.

Breakout-room architecture (3 phase-isolated rooms with orchestrator
forwarding) is documented at [docs/breakout_rooms.md](docs/breakout_rooms.md)
for the same reason.

---

## Hackathon submission checklist

- [x] Public GitHub repository — https://github.com/DeveshValluru/greenlight-ai
- [x] ≥ 3 agents collaborating through Band — we have 7
- [x] Cross-framework demonstration — 3 adapters (Google ADK, LangGraph, CrewAI)
- [x] Multi-model demonstration — 3 Gemini tiers (Flash-Lite, Flash, Pro) routed per workload
- [ ] Cover image
- [ ] Demo video (script in [docs/demo_script.md](docs/demo_script.md))
- [ ] Pitch deck (outline in [docs/pitch_deck.md](docs/pitch_deck.md))
- [ ] Live demo URL (deploy `frontend/app.py` to Streamlit Cloud)

---

## Credits

Built for the Band of Agents Hackathon, June 2026.
Prompt design draws on published research: **MetaGPT** (structured artifact
handoffs), **PROCLAIM 2026** (courtroom-style adversarial debate),
**DebateCV WWW 2026** (opposing debaters), **AgenticSimLaw** (private
reasoning), **Nature 2026** (adversarial-agent safety guardrails), and
**Anthropic 2025–2026** best practices (XML-tagged prompts, self-verification).

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

GreenLight AI is a decision-support tool. It does not constitute financial
or legal advice. Human judgment is essential for all investment decisions.
