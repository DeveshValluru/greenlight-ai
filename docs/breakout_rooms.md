# Breakout-room architecture

GreenLight AI uses **three Band rooms** with phase-isolated participants.
The orchestrator forwards each phase's outputs into the next room as clean
messages, so RedTeam and CRO operate on curated context, not raw debate
noise.

```
┌──────────────────────────────────────────────────────────────────────┐
│ ROOM 1 — GreenLight Briefing                                         │
│ Participants: You + ScriptAnalyst, BudgetAuditor, MarketIntel,       │
│               LegalEagle, TalentScout                                │
│                                                                      │
│ You paste the project package and @mention the 5 specialists.        │
│ They produce structured reports (noisy room, that's OK).             │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
                  Orchestrator captures each report
                  by marker, posts them cleanly into:
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ROOM 2 — GreenLight Cross-Examination                                │
│ Participants: You + RedTeam + 5 specialists (so they can defend)     │
│                                                                      │
│ Room receives 5 clean reports + a trigger to @RedTeam.               │
│ RedTeam reads pristine input, issues challenges, tracks resolutions, │
│ posts CROSS-EXAMINATION SUMMARY.                                     │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
                  Orchestrator captures the summary,
                  forwards 5 reports + summary into:
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ROOM 3 — GreenLight Verdict                                          │
│ Participants: You + CRO                                              │
│                                                                      │
│ Room receives 5 reports + RedTeam summary + a trigger to @CRO.       │
│ CRO synthesizes (Phase 2 revisions take precedence over Phase 1)     │
│ and posts the final scorecard + GREENLIGHT / CONDITIONAL / PASS.     │
└──────────────────────────────────────────────────────────────────────┘
```

## Why this design wins

- **Solves the noise problem.** With a single room, RedTeam and CRO drown
  in retries, user nags, and partial responses. Forwarding gives them
  exactly the 5 final reports.
- **Better demo recording.** Three panes side-by-side show the handoff
  visually — a clear pitch story for the hackathon.
- **Stronger Band showcase.** Demonstrates multi-room coordination plus
  inter-room orchestration — beyond the basic single-room pattern.

## Band setup (one-time, ~10 min)

1. **Create three rooms** in Band UI (`https://app.band.ai/chat` → **+ New Chat**):
   - `GreenLight Briefing`
   - `GreenLight Cross-Examination`
   - `GreenLight Verdict`

2. **Add the right agents to each:**

   | Room                 | Agents to add |
   |----------------------|---------------|
   | GreenLight Briefing  | ScriptAnalyst, BudgetAuditor, MarketIntel, LegalEagle, TalentScout |
   | GreenLight Cross-Examination | RedTeam, ScriptAnalyst, BudgetAuditor, MarketIntel, LegalEagle, TalentScout |
   | GreenLight Verdict   | CRO |

   Use the participants panel toggle (DV avatar in top-right of chat
   header) → click `+` → Agents tab → add by name.

3. **Copy each room ID** from the URL bar (e.g.
   `https://app.band.ai/chat/<UUID>`) into `.env`:
   ```
   BRIEFING_ROOM_ID=<uuid-of-briefing-room>
   CROSS_EXAM_ROOM_ID=<uuid-of-cross-exam-room>
   VERDICT_ROOM_ID=<uuid-of-verdict-room>
   ```

4. **Restart the agents** — they auto-subscribe to all rooms they're
   added to:
   ```powershell
   Ctrl+C
   python run_all_agents.py
   ```

5. **Start the orchestrator** in a second terminal:
   ```powershell
   python -m orchestrator.workflow
   ```
   You should see:
   ```
   🎬 GreenLight orchestrator — 3-ROOM BREAKOUT mode
       briefing:   <uuid>
       cross-exam: <uuid>
       verdict:    <uuid>
   ```

## Running a demo

1. In the **Briefing** room, paste the kickoff message:
   ```
   @ScriptAnalyst @BudgetAuditor @MarketIntel @LegalEagle @TalentScout
   please analyze this project package:

   [paste demo_data/sample_script.txt]
   [paste demo_data/sample_budget.csv]
   [paste demo_data/sample_crew.json]
   ```

2. **Walk away.** The orchestrator drives everything else:
   - Captures each specialist's report (by marker)
   - Forwards all 5 into Cross-Examination
   - Triggers RedTeam
   - Captures the cross-examination summary
   - Forwards everything into Verdict
   - Triggers CRO

3. Check the **Verdict** room for the final scorecard and verdict.

## Single-room fallback

If `BRIEFING_ROOM_ID`, `CROSS_EXAM_ROOM_ID`, and `VERDICT_ROOM_ID` are
unset (or equal), the orchestrator falls back to single-room mode and
uses `GREENLIGHT_ROOM_ID`. All 7 agents work in one room. Useful for
quick tests; not recommended for the recorded demo.

## Caveats

- **REST endpoint uncertainty.** The orchestrator probes 3 endpoint
  shapes for user-side messaging (`/api/v1/chats/{id}/messages`,
  `/api/v1/user/chats/{id}/messages`, `/me/chats/{id}/messages`) and uses
  the first one that returns 200. If none work, check Band's docs or the
  SDK source for the right path and edit `_candidate_endpoints()` in
  `orchestrator/workflow.py`.
- **Long reports may hit Band message-size limits.** If a forwarded
  report exceeds Band's per-message cap, we'll need to chunk it. Not
  encountered in testing so far but worth knowing.
- **The agents see the forwarded reports as new room context.** This is
  what we want — RedTeam reads a clean 5-message room. But it means the
  agents' history of who said what in the Briefing room is lost. The
  audit trail still exists across all three rooms.
