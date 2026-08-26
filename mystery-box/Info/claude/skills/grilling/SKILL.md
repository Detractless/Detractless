---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea before building it. Use when the user says "grill me", "grill this", "stress-test this", "poke holes in this", or asks to think a build through before writing code.
---

Interview the user relentlessly until you reach a shared understanding. Map this
as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose
prerequisites are already settled: the questions you can ask _now_ without
guessing at answers you haven't heard yet. Ask the whole frontier in one round:
number each question and give your recommended answer. Then wait for the user's
answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the
frontier outward and unblock questions that depended on them. Recompute the
frontier and ask the next round. A question whose answer depends on another
question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a
fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find
it; don't ask the user for anything you could look up yourself. Don't block on
it: a running exploration is an unsettled prerequisite, so only the questions
downstream of it wait for the sub-agent to report; ask the rest of the frontier
now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree
visited, nothing left silently assumed. Do not act on it until the user confirms
you have reached a shared understanding.

## Local adaptations

- **The reply template yields during a round.** A round is the numbered Q/➡️
  block above and nothing else — no Verdict, no Verify, no Next wrapped around
  it. The template resumes on the first reply after the frontier empties.
- **Word caps do not apply to rounds.** A question with too little context to
  answer is a wasted round-trip; give the full body.
- **Sub-agents return summaries, not dumps** — a handful of bullets each, the
  same as any other delegated exploration.
- **"go" means take every recommendation** in the open round as written. A bare
  number list ("1 web, 3 no") answers only those and accepts the ➡️ picks for
  the rest.
- **`noplan` ends it immediately** — drop the remaining frontier, state what you
  are assuming in one line, and build.
- **The last round ends with the shared understanding written down**, not just
  agreed in chat: append the settled decisions to `CONTINUATION-NNN.md` before
  the first edit, so the plan survives a reset.

Adapted from https://github.com/mattpocock/skills — `productivity/grilling`.
