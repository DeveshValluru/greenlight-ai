# GreenLight AI — Continuation Handoff

> **Read this file FIRST if you are an AI agent picking up this project.**
> It's a complete snapshot of state, decisions, and next actions as of
> 2026-06-17 (updated post-first-smoke-test), written so you can resume
> work without re-deriving context.

## ⚡ Latest update — first end-to-end agent run worked

ScriptAnalyst smoke test SUCCEEDED at 2026-06-17 12:50 local. The agent
connected, authenticated, and is subscribed to the GreenLight room over
WebSocket. Log highlights:

```
[script_analyst] ScriptAnalyst running on gemini (gemini-2.5-flash)
[httpx] GET https://app.band.ai/api/v1/agent/me → 200
[band.adapters.google_adk] Google ADK adapter started for agent: ScriptAnalyst
[band.runtime.runtime] Starting AgentRuntime for agent cec320bc-59cd-…
[WebSocket] Subscribed to topic: chat_room:99b560b4-bc02-4a04-8bc1-84ed5357921d
[band.agent] Agent started: ScriptAnalyst (band-sdk 1.0.0)
ExecutionContext 99b560b4-…: Synchronized, switching to WebSocket
```

What we learned along the way is captured in §11 (Verified facts and
corrections) below. Read that section before touching adapter code or
REST clients.

---

## 0. How to use this document

You are continuing work on **GreenLight AI**, a 7-agent film investment due
diligence system being built for the Band of Agents Hackathon (lablab.ai).
Submission deadline: **2026-06-19**.

Before doing anything:

1. Read this file end to end (≈10 min).
2. Read the original blueprint at `extracted/blueprint.md` and `extracted/prompts_v2.md`
   in the project root if you need product-level rationale.
3. Run `git status` (if a git repo) — if no git, the project is at:
   `C:\Users\deves\OneDrive\Desktop\GreenlightAI\greenlight-ai\`

Working directory: `C:\Users\deves\OneDrive\Desktop\GreenlightAI\greenlight-ai\`
The user is **Devesh Valluru** (email: devesh.valluru@gmail.com).
His Band handle is **dvallur2** — every @mention in this project uses
`@dvallur2/<handle>` format, NOT `@AgentName`.

---

## 1. The mission

Multi-agent investment committee for film producers. A producer uploads
a project package (script, budget, crew, deal memos). Seven specialized
AI agents collaborate in a Band chat room across three phases:

```
PHASE 1 — Parallel analysis (5 specialists)
  @dvallur2/scriptanalyst   — production complexity
  @dvallur2/budgetauditor   — budget audit
  @dvallur2/marketintel     — comparable films & ROI
  @dvallur2/legaleagle      — IP, guild, insurance
  @dvallur2/talentscout     — team track record

PHASE 2 — Adversarial cross-examination
  @dvallur2/redteam — finds cross-agent contradictions
                       issues formal challenges (C-1, C-2…)
                       tracks resolutions

PHASE 3 — Verdict
  @dvallur2/cro — weighted scorecard
                   GREENLIGHT / CONDITIONAL / PASS
```

Track: **Track 3 — Regulated & High-Stakes Workflows**.
Why this wins: zero competing submissions in film/entertainment, adversarial
debate produces insights no single agent could (e.g. the $1.5M VFX shortfall
emerging only when ScriptAnalyst's shot count is compared against
BudgetAuditor's per-shot allocation).

---

## 2. Architecture decisions already made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework adapters | Google ADK, LangGraph, PydanticAI, CrewAI | 4-way diversity is the hackathon's "Application of Technology" hook |
| LLM providers | Gemini (free) + Groq (free) + Featherless (trial) | Zero cost; Featherless required for partner-prize eligibility |
| LLM_MODE switch | `dev` (all Gemini) vs `demo` (per-agent assignment) | Preserves Featherless trial tokens during dev; switches for recording |
| Agent handle format | `@dvallur2/scriptanalyst` etc. | Band's @mention is namespaced `@user/handle`, not bare `@Agent` |
| Public directory | OFF | Privacy. Personal Registry Access ON so dynamic recruitment works |
| Room type | Single shared room | Audit trail = conversation history (per blueprint) |
| Phase transitions | Polling REST orchestrator | Simpler than WebSocket subscriptions for hackathon |
| SpecialistOnCall | Platform agent (Pro feature) | Enables RedTeam's dynamic-recruitment demo beat |

---

## 3. Current state — what's done and what's NOT

### ✅ Done (do not redo)

1. **Project scaffold** at `greenlight-ai/` with the full file tree
2. **All 7 v2 prompts** in `prompts/` — XML-structured, evidence-cited,
   already patched to use `@dvallur2/<handle>` format
3. **7 agent runtimes** in `agents/` — each wired to its assigned framework
   adapter via `agents/llm_router.py`
4. **Phase orchestrator** in `orchestrator/workflow.py` — polling-based,
   with timeout reminders. Phase 2/3 triggers also use namespaced handles.
5. **Streamlit frontend** in `frontend/` — Upload, Debate (live feed),
   Scorecard pages. `frontend/band_client.py` is the REST helper.
6. **"The Deep Horizon" demo data** in `demo_data/` with seven planted red flags
7. **Launcher** `run_all_agents.py` with graceful shutdown
8. **Docs**: README, `docs/architecture.md`, `docs/pitch_deck.md`,
   `docs/demo_script.md`, `docs/setup_band_agents.md`
9. **7 external agents created on Band**, credentials in `config/agent_config.yaml`
10. **Chat room created** — ID `99b560b4-bc02-4a04-8bc1-84ed5357921d`
11. **All 7 agents added to the room** as participants (verified in UI; count
    showed 8 = user + 7 agents)
12. **`.env` populated** with: Featherless key, Orchestrator (user) API key,
    Band room ID, Band URLs, LLM_MODE=dev
13. **Prompts and code patched** to use `@dvallur2/...` handles everywhere
    that messages get sent to Band (`orchestrator/workflow.py`,
    `frontend/pages/1_Upload.py`, all 7 `prompts/*.md`)

### ⏳ NOT done — required to run the system

1. **`GOOGLE_API_KEY` missing in `.env`** — STILL `replace-me`.
   Get one at https://aistudio.google.com/app/apikey (free, no card).
   This is the ONE remaining blocker for `LLM_MODE=dev` testing.

2. **`GROQ_API_KEY` missing in `.env`** — STILL `replace-me`.
   User reported the Groq site was not loading. Only needed for
   `LLM_MODE=demo`, not for dev. Get at https://console.groq.com/keys
   (free, no card).

3. **SpecialistOnCall NOT created yet**. Needs Band Pro. User started the
   BANDHACK26 promo Stripe checkout in tab `2016832063` but Claude was
   blocked from the Stripe page (payment flow). User must complete it
   themselves. Once Pro is active, create the platform agent at
   `https://app.band.ai/agents/new/internal` with:
   - Name: `SpecialistOnCall`
   - Handle: `specialistoncall`
   - Description: "On-demand specialist for film production topics including
     tax incentives, international co-production, distribution strategy,
     insurance, and union regulations."
   - **Do NOT add it to the GreenLight room.** RedTeam must discover and
     recruit it dynamically — that's the demo beat.

4. **Python deps not installed**. The user will need to run
   `pip install -r requirements.txt` in a venv before agents will start.

5. **No end-to-end smoke test** has been run yet. After Gemini key is in,
   the first thing to do is:
   ```
   python -m agents.script_analyst
   ```
   Then in the Band room post:
   `@dvallur2/scriptanalyst hi — please confirm you can hear me`
   You should get a structured response.

### ⏳ NOT done — needed for submission

6. **Demo video** — script at `docs/demo_script.md` has the exact 4:30
   timeline. Needs to be recorded after end-to-end works.
7. **Pitch deck** — outline at `docs/pitch_deck.md` (6–7 slides). Build
   in Google Slides or similar.
8. **Live demo URL** — deploy `streamlit run frontend/app.py` to
   Streamlit Cloud or Vercel.
9. **GitHub repo** — code is local; not committed/pushed yet.
10. **lablab.ai submission** — title, description, video URL, GitHub URL,
    demo URL. Deadline 2026-06-19.

---

## 4. File map

```
greenlight-ai/
├── .env                    ← LOCAL secrets (gitignored). Already populated
│                             except GOOGLE_API_KEY and GROQ_API_KEY.
├── .env.example            ← Template for new clones
├── .gitignore
├── README.md               ← Hackathon-facing
├── LICENSE                 ← MIT
├── pyproject.toml
├── requirements.txt
├── run_all_agents.py       ← Launches all 7 agent subprocesses
│
├── agents/                 ← One file per agent + the LLM router
│   ├── __init__.py
│   ├── llm_router.py       ← KEY FILE. Provider routing per LLM_MODE.
│   │                         Exposes get_config(), load_prompt(),
│   │                         load_agent_config(), band_endpoints().
│   ├── script_analyst.py   ← Google ADK adapter + Gemini
│   ├── budget_auditor.py   ← LangGraph adapter + Groq Llama 3.3
│   ├── market_intel.py     ← Google ADK + Gemini
│   ├── legal_eagle.py      ← PydanticAI + Featherless Llama
│   ├── talent_scout.py     ← LangGraph + Groq Qwen
│   ├── red_team.py         ← Google ADK + Gemini
│   └── cro.py              ← CrewAI + Featherless DeepSeek R1
│
├── prompts/                ← v2 prompts (XML-structured, few-shot, handle-patched)
│   ├── script_analyst.md
│   ├── budget_auditor.md
│   ├── market_intel.md
│   ├── legal_eagle.md
│   ├── talent_scout.md
│   ├── red_team.md         ← Includes Step 2.5 dynamic-recruitment instructions
│   └── cro.md
│
├── orchestrator/
│   ├── __init__.py
│   └── workflow.py         ← Polls Band room, triggers Phase 2 and 3
│                             Uses AGENT_HANDLES map for namespaced retries.
│
├── frontend/               ← Streamlit dashboard
│   ├── __init__.py
│   ├── app.py              ← Home / landing page
│   ├── band_client.py      ← Thin REST wrapper (fetch_messages, post_message)
│   └── pages/
│       ├── __init__.py
│       ├── 1_Upload.py     ← Posts kickoff message with @dvallur2/... mentions
│       ├── 2_Debate.py     ← Auto-refreshing message feed with agent colors
│       └── 3_Scorecard.py  ← Parses CRO output, radar chart via Plotly
│
├── demo_data/
│   ├── sample_script.txt   ← "The Deep Horizon" treatment, 110 pages
│   ├── sample_budget.csv   ← $7.26M budget with 7 planted red flags
│   ├── sample_crew.json    ← Director with no sci-fi experience, etc.
│   └── sample_contracts.txt← Deal memos with PENDING signatory status
│
├── config/
│   ├── agent_config.yaml          ← REAL Band UUIDs + API keys (gitignored)
│   └── agent_config.yaml.example  ← Template
│
└── docs/
    ├── HANDOFF.md             ← THIS FILE
    ├── architecture.md
    ├── pitch_deck.md
    ├── demo_script.md
    └── setup_band_agents.md
```

---

## 5. Critical implementation details

### 5.1 The handle format gotcha

Band's @mention is `@<username>/<agent_handle>`. The user is `dvallur2`.
All 7 agents have lowercase handles:
- `scriptanalyst`, `budgetauditor`, `marketintel`, `legaleagle`,
  `talentscout`, `redteam`, `cro`, plus `specialistoncall` (pending)

If you write new agent-facing code or messages, ALWAYS use the
`@dvallur2/<handle>` form, never `@ScriptAnalyst`.

### 5.2 LLM_MODE switching

`agents/llm_router.py` defines two modes:
- `dev` — every agent routes through Gemini 2.5 Flash. Use for development
  to avoid burning the 100K Featherless trial token budget.
- `demo` — per-agent assignment per blueprint addendum FIX 8:
  ```
  Gemini       ← ScriptAnalyst, MarketIntel, RedTeam
  Groq Llama   ← BudgetAuditor
  Groq Qwen    ← TalentScout
  Featherless  ← LegalEagle (Llama), CRO (DeepSeek R1)
  ```
- Each agent file calls `get_config(<agent_name>)` once at startup; the
  router resolves the right `base_url`, `model`, `api_key`.
- Missing/placeholder keys raise `EnvironmentError` at startup — agents
  fail loudly, no half-configured runs.

### 5.3 The orchestrator

`orchestrator/workflow.py` polls Band REST every 5s for messages.
It detects per-agent completion by string markers in their reports:
- ScriptAnalyst → "FEASIBILITY SCORE"
- BudgetAuditor → "BUDGET ADEQUACY SCORE"
- MarketIntel → "COMMERCIAL VIABILITY SCORE"
- LegalEagle → "LEGAL RISK SCORE"
- TalentScout → "TALENT RISK SCORE"

When all 5 are detected → posts Phase 2 trigger to @dvallur2/redteam.
When RedTeam posts "CROSS-EXAMINATION SUMMARY" → triggers @dvallur2/cro.
When CRO posts "VERDICT:" → orchestration ends.

Reminders are capped (`MAX_REMINDERS_PER_AGENT = 2`) so a silent agent
doesn't get spammed.

### 5.4 The Streamlit frontend

Run with `streamlit run frontend/app.py` from the repo root.
Pages auto-discover from `frontend/pages/`. Imports use the flat form
(`from band_client import …`) because Streamlit puts the script directory
on `sys.path`, not the repo root.

`frontend/band_client.py` reads credentials from Streamlit secrets first,
falls back to env vars. For local dev with `.env`, the env-var fallback
works fine.

### 5.5 Adapter API guesses to verify

When wiring the Band SDK, the following may need adjustment against the
real SDK shape (I inferred from tutorial links in the blueprint):
- `from thenvoi import Agent` and `from thenvoi.adapters import …` —
  the package may actually be `band_sdk` or similar. Check
  `pip show band-sdk` after install.
- `GoogleADKAdapter(model=..., api_key=..., base_url=..., custom_section=...)` —
  parameter names may differ.
- `PydanticAIAdapter(agent=...)` — may take a model directly instead.
- `CrewAIAdapter(crew_agent=...)` — may take a `Crew` or different shape.
- REST endpoint `/me/chats/{room_id}/messages` — verify against
  https://docs.band.ai/api/introduction once you have a user API key
  working.

---

## 6. What to do next — concrete action queue

In priority order:

### 6.1 (Easy, unblocks everything) Get the Gemini key

1. User opens https://aistudio.google.com/app/apikey
2. Generate API key (one click; uses Google account)
3. Paste into `.env` at `GOOGLE_API_KEY=...`

### 6.2 (5 min) Smoke-test one agent

```bash
cd C:\Users\deves\OneDrive\Desktop\GreenlightAI\greenlight-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m agents.script_analyst
```

Expected:
```
[script_analyst] ScriptAnalyst running on gemini (gemini-2.5-flash). Ctrl+C to stop.
```

Then in the Band UI room post:
`@dvallur2/scriptanalyst hi — please confirm you can hear me`

You should get a structured response. If you get an error from the SDK,
the import paths or adapter constructor params may need adjustment
(see §5.5).

### 6.3 (5 min) Launch all 7 agents

Once one agent is confirmed working:
```bash
python run_all_agents.py
```

### 6.4 (User action) Finish BANDHACK26 promo, then SpecialistOnCall

If/when the user confirms Band Pro is active:
1. Navigate to `https://app.band.ai/agents/new/internal`
2. Create the platform agent named `SpecialistOnCall`
   (see §3 item 3 for description)
3. Do NOT add it to the GreenLight room

### 6.5 First end-to-end run

In the Band room, paste the "The Deep Horizon" demo data using the
Streamlit Upload page, or manually post the kickoff message. Watch
Phase 1 reports populate. If the orchestrator is running
(`python -m orchestrator.workflow`), Phase 2 and 3 will trigger
automatically.

### 6.6 Iterate on prompts if needed

If an agent's output drifts off-format, the most likely fix is in the
matching `prompts/<agent>.md`. The XML structure and verification
checklists are the levers.

### 6.7 Record the demo video

Follow `docs/demo_script.md` exactly. Recommended: OBS Studio for
screen recording + voiceover. Keep total length 4–5 minutes.

### 6.8 Build the pitch deck

Use `docs/pitch_deck.md` as the outline. Google Slides or similar.

### 6.9 Deploy and submit

- Push code to a public GitHub repo
- Deploy frontend to Streamlit Cloud (https://share.streamlit.io)
  with secrets `BAND_REST_URL`, `GREENLIGHT_ROOM_ID`,
  `ORCHESTRATOR_API_KEY`
- Submit on lablab.ai with the 5 deliverables

---

## 7. Known issues / gotchas

1. **Stripe domain is blocked** for safety. The user must complete any
   billing flow themselves. Do not retry Stripe pages — they will
   continue to fail and lock the tab.
2. **Band participants panel** — the toggle button is a tiny avatar with
   a count badge in the top-right of the chat header. Easy to miss.
   The "Agents" tab inside the panel is mis-classified in Claude-in-Chrome's
   accessibility tree as the same as the sidebar "Agents" link; clicking
   it via `ref_*` navigates the whole page. Use direct screen coordinates
   if you need to drive it.
3. **Tags on Band agents** are limited to 7 characters each. "duediligence"
   (12 chars) will be rejected. Use "film, script" etc.
4. **Form inputs may not trigger React onChange** when set via
   `form_input` tool. Use `triple_click` + `type` if the page doesn't
   update.
5. **Adapter parameter names** — see §5.5. May need to read
   `thenvoi.adapters.<Name>.__init__` once the SDK is installed.
6. **Featherless trial is 3 days from sign-up** and 100K output tokens
   total. Don't burn it in dev — `LLM_MODE=dev` keeps it untouched.
7. **Groq site was reported as unreachable** by the user. May be a
   regional issue. The system runs fine in dev mode without Groq;
   only blocks demo-mode recording.

---

## 8. Memory / continuity

Persistent memory for this project is at:
`C:\Users\deves\.claude\projects\C--Users-deves-OneDrive-Desktop-GreenlightAI\memory\`

Specifically `project_greenlight_ai.md` holds the long-form project
context. Update it if major facts change (e.g. submission completed,
provider swap, scope change).

---

## 9. If something is broken

- **Agent won't start**: Almost certainly a missing key. Check `.env`
  for `replace-me` placeholders. Run `python -c "from agents.llm_router
  import get_config; print(get_config('script_analyst'))"` to verify
  routing.
- **Agent connects to Band but never responds to mentions**: The handle
  in the prompt and the @mention in the room must match exactly,
  including case. Band's handle is case-sensitive in `@user/handle`
  form. Check `config/agent_config.yaml`'s `handle:` field against
  what you typed.
- **Orchestrator times out repeatedly**: Check whether agents are
  actually posting (look in the Band room UI). If yes but no Phase 2
  trigger, the per-agent completion markers in `PHASE1_MARKERS` may
  not match what the agent is actually producing — adjust the prompt
  to enforce the marker, or relax the marker.
- **Streamlit shows "Could not load messages"**: `ORCHESTRATOR_API_KEY`
  or `GREENLIGHT_ROOM_ID` is missing from `.env` or Streamlit secrets,
  or the Band REST endpoint shape has changed.

---

## 10. A note for the next agent

This project is currently in **integration-and-test** phase, not
greenfield. The scaffold is solid; the remaining work is:

1. Getting the Gemini key in (user task, 30 seconds)
2. Verifying the Band SDK adapter calls actually work (10–60 min,
   depending on SDK surface)
3. Running an end-to-end test (10 min)
4. Recording video, building deck, deploying, submitting (½–1 day)

The deadline is **2026-06-19**. Prioritize ruthlessly: a working
4-agent demo beats a half-broken 7-agent demo. Drop SpecialistOnCall
or one specialist before you drop the end-to-end run.

Good luck.

— Claude (Opus 4.7), session of 2026-06-15 → 2026-06-17

---

## 11. Verified facts and corrections (post-smoke-test)

These items were either wrong in the blueprint and have been fixed, or
were uncertain at scaffold time and have now been confirmed.

### 11.1 Band SDK import path

| Wrong (blueprint) | Right (verified) |
|-------------------|------------------|
| `from thenvoi import Agent` | `from band import Agent` |
| `from thenvoi.adapters import …` | `from band.adapters import …` |
| `from thenvoi.config import …` | n/a — load YAML directly |

The PyPI package is `band-sdk` but the import name is `band`.
A sibling package `thenvoi_rest` is also installed and used internally
by the SDK as the auto-generated REST client. Do not import from
`thenvoi_rest` directly.

### 11.2 Band URLs

| Wrong (blueprint) | Right (verified, also SDK defaults) |
|-------------------|--------------------------------------|
| `wss://ws.band.ai` | `wss://app.band.ai/api/v1/socket/websocket` |
| `https://api.band.ai` | `https://app.band.ai` |

`api.band.ai` does not exist (DNS NXDOMAIN). Confirmed via the
`Agent.create` default-arg inspection:

```python
inspect.signature(Agent.create)
# (adapter, agent_id, api_key,
#  ws_url='wss://app.band.ai/api/v1/socket/websocket',
#  rest_url='https://app.band.ai', ...)
```

`.env`, `agents/llm_router.py:band_endpoints()`,
`orchestrator/workflow.py`, and `frontend/band_client.py` have all
been updated.

### 11.3 Band REST API paths (for orchestrator and frontend)

The orchestrator and frontend post to Band as a USER (not as an agent).
The current code uses `/me/chats/{room_id}/messages` — that path is a
**GUESS** and probably wrong. From the agent side, the SDK uses:

- `GET /api/v1/agent/me`
- `GET /api/v1/agent/chats?page=…`
- `GET /api/v1/agent/chats/{room_id}/messages?status=processing&page=…`
- `GET /api/v1/agent/chats/{room_id}/messages/next`

The corresponding user-facing path is **most likely** something like:

- `GET  /api/v1/chats/{room_id}/messages`  (best guess)
- `POST /api/v1/chats/{room_id}/messages`

…but this has NOT been verified. If the Streamlit Debate page or the
orchestrator fails with 404 / 401, that's why. The cleanest fix is to
read the SDK source under `.venv/Lib/site-packages/band/` or
`.venv/Lib/site-packages/thenvoi_rest/` to find the real user endpoint.

### 11.4 Adapter constructors

`GoogleADKAdapter` signature (verified):

```python
GoogleADKAdapter(
    model: str = 'gemini-2.5-flash',
    system_prompt: str | None = None,
    custom_section: str | None = None,
    enable_execution_reporting: bool = False,
    enable_memory_tools: bool = False,
    history_converter: GoogleADKHistoryConverter | None = None,
    additional_tools: list[CustomToolDef] | None = None,
    max_history_messages: int = 50,
    max_transcript_chars: int = 100000,
    features: AdapterFeatures | None = None,
)
```

Key differences from blueprint guess:
- **NO `api_key=`** — google-adk reads `GOOGLE_API_KEY` from env
- **NO `base_url=`** — google-adk hits Gemini's default endpoint
- `enable_execution_reporting=True` works but emits a DeprecationWarning.
  Preferred:
  `features=AdapterFeatures(emit={Emit.EXECUTION}, capabilities={Capability.MEMORY})`

In `agents/script_analyst.py` we set `os.environ.setdefault("GOOGLE_API_KEY",
cfg["api_key"])` before instantiating the adapter. The other Google-ADK
agents (`market_intel.py`, `red_team.py`) still pass `api_key=` and
`base_url=` — **THEY WILL FAIL THE SAME WAY**. Apply the same fix:

```python
import os
os.environ.setdefault("GOOGLE_API_KEY", cfg["api_key"])
adapter = GoogleADKAdapter(
    model=cfg["model"],
    custom_section=load_prompt(...),
    enable_execution_reporting=True,
)
```

The other adapters (`LangGraphAdapter`, `PydanticAIAdapter`,
`CrewAIAdapter`) have NOT been signature-verified yet. When you fix
them, run:

```powershell
python -c "import inspect; from band.adapters import <Name>; print(inspect.signature(<Name>.__init__))"
```

…to discover the real params before editing.

### 11.5 `Agent.create` signature (verified)

```python
Agent.create(
    adapter,                                    # required
    agent_id: str,                              # required
    api_key: str,                               # required (BAND agent API key)
    ws_url='wss://app.band.ai/api/v1/socket/websocket',
    rest_url='https://app.band.ai',
    config: AgentConfig | None = None,
    session_config: SessionConfig | None = None,
    contact_config: ContactEventConfig | None = None,
    on_participant_added: Callback | None = None,
    on_participant_removed: Callback | None = None,
    preprocessor: Preprocessor | None = None,
)
```

The existing agent files call this correctly.

### 11.6 Dependency install gotchas

- `pip install -r requirements.txt` hits `resolution-too-deep` on the
  combined graph. Install in batches:
  ```
  pip install "band-sdk[anthropic,langgraph,crewai,pydantic-ai]"
  pip install google-adk
  pip install streamlit pandas plotly
  pip install python-dotenv pyyaml httpx langchain-openai openai pypdf python-multipart
  ```
- After `google-adk` install, pip warns about conflicting pins:
  - `crewai 1.14.3` wants `pydantic ~=2.11.9`, `opentelemetry-api ~=1.34.0`,
    `opentelemetry-sdk ~=1.34.0`
  - `google-adk 2.2.0` bumps these to `pydantic 2.13.4`, `opentelemetry 1.41.1`
  - **Likely impact:** crewai-based **CRO agent** may break at runtime.
    If it does, downgrade selectively:
    ```
    pip install "pydantic~=2.11.9" "opentelemetry-api~=1.34.0" "opentelemetry-sdk~=1.34.0"
    ```
    (And accept the inverse warning from google-adk.) Or pin google-adk
    to a version compatible with crewai's older requirements.

### 11.7 Discovered side-effect

When ScriptAnalyst connected, it auto-subscribed to TWO rooms:
- `99b560b4-bc02-4a04-8bc1-84ed5357921d` (the GreenLight room we created)
- `adebb057-d4a2-446f-b030-73143b00e9c7` (a second room — likely Band's
  default agent-only room or another room the agent was added to)

If you see unrelated messages, that's why. Not a bug.

### 11.7c Breakout-room architecture added (2026-06-18)

The orchestrator at `orchestrator/workflow.py` was rewritten to support
3-room phase isolation:

- **Briefing** room → 5 specialists + human
- **Cross-Examination** room → RedTeam + 5 specialists
- **Verdict** room → CRO only

The orchestrator captures each agent's full report message (by marker
string) from one room and reposts it as a clean message in the next room.
This solves the noise problem we hit in single-room mode: RedTeam was
hallucinating "I only have ScriptAnalyst's report" because the other 5
reports were outside its `max_history_messages` window.

`.env` gained three vars: `BRIEFING_ROOM_ID`, `CROSS_EXAM_ROOM_ID`,
`VERDICT_ROOM_ID`. If unset, the orchestrator falls back to single-room
mode using `GREENLIGHT_ROOM_ID`. Full setup steps in
`docs/breakout_rooms.md`.

REST endpoint for user-side messaging is still uncertain — the
orchestrator tries 3 candidate URL shapes and uses whichever returns 200.
If POSTs fail, check Band SDK source for the right shape and edit
`_candidate_endpoints()`.

### 11.7b LegalEagle swapped from PydanticAI to LangGraph (2026-06-17)

PydanticAI's strict structured-output validation caused two production
issues in the Band room:

- `[[uuid]]` placeholders leaked into agent replies, which Band rejected
  as malformed mentions
- LegalEagle hallucinated an identity crisis ("I am not LegalEagle…")

We swapped `agents/legal_eagle.py` to use `LangGraphAdapter` (same
pattern as BudgetAuditor and TalentScout — both stable). Effects:

- Same project structure: only the one agent file changed
- Same agent UUID / handle on Band — no re-registration needed
- Framework count drops from 4 → 3 (Google ADK, LangGraph, CrewAI).
  Update the pitch deck and demo script accordingly.
- README updated. Prompt at `prompts/legal_eagle.md` unchanged — the
  XML-structured markdown prompt works equally well with LangGraph.

### 11.8 Remaining concrete TODOs after this checkpoint

1. **Apply the same `GOOGLE_API_KEY` env-var pattern** to
   `agents/market_intel.py` and `agents/red_team.py` (same adapter,
   same fix).
2. **Verify and fix** `LangGraphAdapter` signature for
   `agents/budget_auditor.py` and `agents/talent_scout.py`.
3. **Verify and fix** `PydanticAIAdapter` signature for
   `agents/legal_eagle.py`.
4. **Verify and fix** `CrewAIAdapter` signature for `agents/cro.py`.
5. **Find the user-side REST paths** for orchestrator/frontend
   (§11.3). Easiest: search the SDK source for the user agent equivalent.
6. **Post the test @mention** in the Band UI room
   (`@dvallur2/scriptanalyst hi`) and confirm a structured reply.
7. **Then** run `python run_all_agents.py` once all 7 adapter calls
   are patched.

### 11.9 Useful inspection commands

```powershell
# Discover real installed module names
python -c "import pkgutil; [print(m.name) for m in pkgutil.iter_modules() if 'band' in m.name.lower() or 'envoi' in m.name.lower()]"

# Inspect any adapter signature
python -c "import inspect; from band.adapters import GoogleADKAdapter as A; print(inspect.signature(A.__init__))"

# Inspect Agent.create
python -c "import inspect; from band import Agent; print(inspect.signature(Agent.create))"

# What REST endpoints does the agent SDK call?
python -c "import inspect, band.runtime.platform_runtime as p; print(inspect.getsource(p.PlatformRuntime))" | findstr /R "api/v1"
```

### 11.10 Useful links (verified)

- Band app + room (your room): https://app.band.ai/chat/99b560b4-bc02-4a04-8bc1-84ed5357921d
- Band agents page: https://app.band.ai/agents
- Band docs: https://docs.band.ai
- Hacker guide: https://www.band.ai/hacker-guide
- Gemini key: https://aistudio.google.com/app/apikey
- Groq key: https://console.groq.com/keys
- Featherless: https://featherless.ai
- Featherless setup guide: https://drive.google.com/file/d/1MNqSDfHbNnjTNaTseAqqyjsXRtjergQp/view
- lablab.ai submission: https://lablab.ai/ai-hackathons/band-of-agents-hackathon
