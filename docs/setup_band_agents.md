# Band agent registration — step-by-step

You need to create eight things on Band before the system can run:

1. Seven **External Agents** (one for each agent file in `agents/`)
2. One **Platform Agent** named `@SpecialistOnCall` for dynamic recruitment
3. One **Chat Room** where they all collaborate

This guide walks through each step.

---

## 1. Sign up & promo code

1. Go to https://app.band.ai and create a free account.
2. *(Optional)* Apply promo code **BANDHACK26** at
   https://www.band.ai/manage-billing for free Band Pro (1 month).

---

## 2. Register the seven external agents

For each agent in the table below:

1. Go to https://app.band.ai/agents
2. Click **New Agent → External Agent**
3. Use the exact name shown below. The name becomes the @mention handle —
   if you call it `Script Analyst` instead of `ScriptAnalyst`, the prompts
   will break.
4. Paste the description.
5. Click **Save**. Copy the **Agent UUID** and **API Key** (the key is
   shown only once — copy it immediately).
6. Paste both into `config/agent_config.yaml` under the matching short name.

| Name (handle) | Short name (yaml key) | Description |
|----|----|----|
| `ScriptAnalyst` | `script_analyst` | Senior film production analyst. Breaks down screenplays into production complexity, VFX counts, locations, and shoot days for investment due diligence. |
| `BudgetAuditor` | `budget_auditor` | Forensic production accountant. Audits film budgets for red flags, cross-references against script requirements, and validates contingency and completion bond coverage. |
| `MarketIntel` | `market_intel` | Film industry market analyst. Researches comparable films and produces revenue projections and commercial risk analysis. |
| `LegalEagle` | `legal_eagle` | Entertainment attorney. Reviews IP chain of title, guild compliance, and required insurance and bond protections. |
| `TalentScout` | `talent_scout` | Talent packaging analyst. Evaluates director, writer, producer, and cast track records to assess execution risk. |
| `RedTeam` | `red_team` | Devil's Advocate. Cross-examines the five specialists, issues formal challenges, tracks resolutions, and escalates unresolved risks to the CRO. |
| `CRO` | `cro` | Chief Risk Officer. Synthesizes all findings (post-cross-examination) into the final weighted scorecard and GREENLIGHT / CONDITIONAL / PASS verdict. |

---

## 3. Register the on-call specialist (platform agent)

The blueprint addendum's "dynamic recruitment" trick needs one **platform
agent** that lives on Band itself rather than as an external WebSocket
client. RedTeam can discover and add this agent into the room mid-debate.

1. Go to https://app.band.ai/agents
2. Click **New Agent → Platform Agent** (not External)
3. Name: `SpecialistOnCall`
4. Description: *"On-demand specialist for film production topics including
   tax incentives, international co-production, distribution strategy,
   insurance, and union regulations."*
5. Use any model Band provides on its free tier — Gemini Flash is fine.
6. **Do NOT add it to the GreenLight room.** It must be discoverable but
   not present until RedTeam recruits it during the demo.

---

## 4. Create the chat room

1. Go to https://app.band.ai → **New Chat Room**
2. Name: `GreenLight: <project title>` — e.g. `GreenLight: The Deep Horizon`
3. Add all seven external agents as participants (do **not** add
   `SpecialistOnCall` — that's the recruitment hook).
4. Add yourself as the human producer.
5. Open the room URL and copy the room ID (the long alphanumeric segment).
6. Paste it into `.env` as `GREENLIGHT_ROOM_ID`.

---

## 5. Get an orchestrator API key

The orchestrator and the Streamlit frontend post messages to the room
*as a human user* (not as one of the agents). You need a user API key:

1. Go to https://app.band.ai/settings → API keys
2. Generate a key and copy it.
3. Paste it into `.env` as `ORCHESTRATOR_API_KEY`.

---

## 6. Smoke-test one agent

Before launching all seven, verify the wiring with just `ScriptAnalyst`:

```bash
python -m agents.script_analyst
```

You should see:
```
[script_analyst] ScriptAnalyst running on gemini (gemini-2.5-flash). Ctrl+C to stop.
```

Then, from the Band UI, post in the room:
```
@ScriptAnalyst Hi — please confirm you can see me.
```

You should get a structured response. If you do, you're ready to launch
all seven with `python run_all_agents.py`.

---

## Troubleshooting

**"Missing GOOGLE_API_KEY for agent 'script_analyst'"**
You haven't filled in `.env` with a real Gemini key. Get one at
https://aistudio.google.com/app/apikey.

**"agent_config.yaml entry for 'script_analyst' has placeholder values"**
You copied the example file but didn't replace the placeholder UUIDs.
Open `config/agent_config.yaml` and paste the real Band UUID/key.

**Agent connects but doesn't respond to @mentions**
Check that the name you used when creating the agent on Band exactly
matches the handle in `prompts/` (`@ScriptAnalyst`, with that exact
capitalization). Band's @mention routing is case-sensitive.

**Featherless errors during demo recording**
The trial is 3 days / 100K output tokens. If you've exhausted it, switch
`LLM_MODE=dev` in `.env` to reroute LegalEagle and CRO through Gemini.
You'll lose the partner-prize qualifier but the demo will still run.
