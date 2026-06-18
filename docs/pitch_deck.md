# Pitch deck outline — GreenLight AI

Target length: 6–7 slides, 90 seconds of voiceover per slide for the demo
video. Total runtime ≈ 10 minutes if presenting live, ≈ 4–5 minutes in the
hackathon video.

---

## Slide 1 — Hook

**Title:** Film investors lose billions on projects that should never have
been greenlit.

**Visual:** Title card. Tagline: *"The AI investment committee that never sleeps."*

---

## Slide 2 — The problem

- Film financing is high-stakes: $5M–$50M per project.
- Due diligence is fragmented across separate consultants (script doctor,
  budget auditor, lawyer, market analyst, talent agent).
- No single human reads *all* the documents and *all* the consultant reports
  end to end. Cross-discipline red flags slip through.
- Real example: a $7M sci-fi thriller with $0 for a marine unit and $0 for
  E&O insurance — both visible in the budget, both invisible to anyone
  reading only the budget without the script.

---

## Slide 3 — The solution

GreenLight AI assembles a virtual investment committee of seven AI agents
inside a single Band chat room.

- Five specialists (script, budget, market, legal, talent) work in parallel.
- A Red Team agent cross-examines them for contradictions.
- A Chief Risk Officer synthesizes everything into a verdict.

The killer feature is the **adversarial cross-examination** in Phase 2.
That's where the $1.5M VFX shortfall on "The Deep Horizon" surfaces — not
from any single agent's report, but from comparing the script's shot count
against the budget's per-shot allocation.

---

## Slide 4 — Architecture

Diagram showing the three phases with Band at the center.
- **Phase 1:** Parallel @mention fan-out to 5 specialists
- **Phase 2:** @RedTeam issues formal challenges (C-1, C-2, …); challenged
  agents revise; RedTeam tracks resolutions
- **Phase 3:** @CRO weighted scorecard

Highlight: **4 framework adapters** (Google ADK, LangGraph, PydanticAI,
CrewAI) and **3 LLM providers** (Gemini, Groq, Featherless) all
collaborating in one room. This is exactly the cross-framework /
cross-provider story Band is built for.

---

## Slide 5 — Live demo result

Screenshot of the scorecard for "The Deep Horizon":
- Verdict: 🟡 **CONDITIONAL** at 52/100
- Top finding: **$1.5M VFX shortfall surfaced via cross-agent examination**
- Three of the five red flags were only catchable by reading two reports
  against each other — exactly what Band enables.

Voiceover beat: *"That number didn't come from the budget agent. It didn't
come from the script agent. It came from the Red Team agent comparing them."*

---

## Slide 6 — Why Band

- @mention routing → parallel work without orchestration code
- Agent-to-agent mentions → adversarial debate is the same primitive as
  human-to-agent
- Participant tools → @RedTeam can recruit @SpecialistOnCall mid-debate
- Persistent room → the message history *is* the audit trail
- SDK adapter layer → frameworks-as-implementation-detail, the *agents* are
  the API

---

## Slide 7 — Market & next steps

- Global film production: $100B+ annually; financing: $30B+ annually
- No AI-native competitor in this vertical
- Extends naturally to: TV / streaming greenlighting, commercial production,
  real-estate development, infrastructure financing — any domain with
  multi-document, multi-discipline due diligence
- Available today as an open-source reference implementation. PR welcome.

---

## Voiceover talking points

- *"Seven agents, four frameworks, three providers, one Band room. Zero
  vendor lock-in."*
- *"The investor sees the full debate. The audit trail is the conversation."*
- *"The AI investment committee that never sleeps."*
