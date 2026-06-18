# Architecture

GreenLight AI is a 3-phase, 7-agent due-diligence system coordinated entirely
through a single Band chat room. Band provides the message bus, @mention
routing, agent-to-agent communication, and the implicit audit trail (every
turn of the analysis is recorded in the room).

## Phase model

```
PHASE 1 — PARALLEL ANALYSIS
══════════════════════════════════════════════════════════
  Human posts the project package.
  All 5 Phase 1 specialists are @mentioned in the same message.
  Band routes the message to each specialist's WebSocket connection.
  Each specialist reads the package, executes private reasoning, then
  posts its structured report back into the room.

PHASE 2 — ADVERSARIAL CROSS-EXAMINATION
══════════════════════════════════════════════════════════
  Orchestrator (or human) @mentions @RedTeam once all 5 reports are detected.
  @RedTeam reads the full thread, runs the cross-reference scan
  (5 agent pairs × N findings), and posts 3–7 formal challenges.
  Each challenge @mentions a single specialist; that specialist either
  REVISES (acknowledges the contradiction) or DEFENDS (cites evidence).
  @RedTeam tracks each challenge as RESOLVED, PARTIAL, or UNRESOLVED.

PHASE 3 — VERDICT
══════════════════════════════════════════════════════════
  Orchestrator (or human) @mentions @CRO.
  @CRO reads the entire conversation, applies the weighted scoring
  rubric (using post-revision scores), and posts the scorecard +
  verdict (GREENLIGHT / CONDITIONAL / PASS).
```

## Why Band specifically

| Capability | How GreenLight uses it |
|------------|------------------------|
| Chat rooms | Single shared context for all 7 agents — everyone reads everything |
| @mention routing | Agents only get woken up when their handle is mentioned (no broadcast spam) |
| Agent-to-agent mentions | @RedTeam mentions @BudgetAuditor; @CRO mentions all specialists — same primitive |
| Participant tools | @RedTeam dynamically discovers and recruits @SpecialistOnCall mid-debate |
| Persistent room | The full message history *is* the audit trail — no separate logging layer |
| WebSocket SDK | Each agent process maintains a single long-lived connection |

## Framework diversity

| Adapter | Agents | Why this adapter |
|---------|--------|------------------|
| Google ADK | @ScriptAnalyst, @MarketIntel, @RedTeam | Native fit for Gemini; ADK's tool-use + reasoning loop matches what these agents need |
| LangGraph | @BudgetAuditor, @TalentScout | State machine + tool calling, good for numeric audit and lookup-heavy talent work |
| PydanticAI | @LegalEagle | Type-safe structured output is well-suited to legal compliance tables |
| CrewAI | @CRO | Role-based reasoning fits the "synthesize multiple specialist reports" pattern |

All four adapters live behind the same Band agent runtime, which is exactly
what the hackathon's "Application of Technology" criterion rewards.

## Provider routing

```
LLM_MODE=dev   → all agents → Gemini 2.5 Flash (preserves Featherless trial)
LLM_MODE=demo  → per-agent assignment:
                   Gemini      ← ScriptAnalyst, MarketIntel, RedTeam
                   Groq        ← BudgetAuditor (Llama), TalentScout (Qwen)
                   Featherless ← LegalEagle (Llama), CRO (DeepSeek R1)
```

The router lives in `agents/llm_router.py`. Each agent calls
`get_config(<name>)` once at startup; the router returns the resolved
`base_url`, `model`, and `api_key` for the current mode. No agent file
contains a hard-coded provider.

## Anti-hallucination protocol

Every agent's prompt enforces:

1. **Evidence-cited assertions** — every claim references a specific source
   line from the input documents.
2. **Confidence levels** — HIGH / MEDIUM / LOW on every finding.
3. **"DATA NOT PROVIDED"** — agents must surface gaps rather than fill them.
4. **Self-verification checklist** — every prompt ends with a `[ ]` checklist
   the agent walks through before posting.
5. **RedTeam guardrails** — challenges must be evidence-grounded and
   falsifiable; no rhetorical attacks.

These come from MetaGPT, PROCLAIM, DebateCV, AgenticSimLaw, and Anthropic's
published prompting guidance. See `prompts_v2.md` (in the project root's
zip-extracted context) for the full research bibliography.

## Failure modes the design accepts

- **A specialist fails to post.** Orchestrator times out after 5 minutes and
  posts a single retry. @CRO marks the missing component as `N/A` and
  downgrades the verdict by a small fixed penalty rather than fabricating.
- **A provider rate-limits.** Each agent fails loudly on missing/invalid
  keys at startup so partial runs don't masquerade as complete.
- **Featherless trial expires mid-run.** Switching `LLM_MODE=dev` reroutes
  everything to Gemini without code changes.
- **RedTeam hallucinates a challenge.** Guardrails in the prompt + the
  challenged specialist's evidence-based rebuttal protocol catch this; the
  challenge is then logged as `UNRESOLVED` rather than counted as confirmed.
