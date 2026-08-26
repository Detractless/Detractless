---
name: verify-work
description: >
  Adversarial self-verification of work no human watched, executed as a multi-agent workflow rather
  than by hand: independent refute-by-default passes over the artifact through several distinct lenses
  (correctness, completeness, fail-open, reproducibility, disposition, quantitative), independent
  adjudication of every finding, dead ends recorded as "X failed BECAUSE Y", and looping until dry-out.
  Use whenever you are about to declare non-trivial work done — a feature or refactor finished, an
  audit or review completed, files merged or migrated, research synthesized, a script's output believed
  — and whenever the user says "check your work", "verify this", "are you sure", "did you actually test
  it", or is running you unattended (overnight jobs, batch passes, background agents, long autonomous
  loops). Also trigger BEFORE reporting any result you did not literally observe being produced, and
  before building any checker, gate, scanner, or test harness whose passing you intend to treat as
  evidence. Do NOT trigger for single-file trivial edits, work the user is watching step by step,
  questions with no artifact to verify, or as a second pass over something already verified under this
  protocol.
---

# Verify work

Verification that the builder runs on itself is not verification. This skill exists because the
expensive failures are not wrong answers — they are wrong answers that *looked* checked.

**This skill executes as a workflow.** The loop, the fan-out, and the termination condition are code,
not prose you follow by hand. Hand-running this protocol drifts: rounds get deduplicated by memory,
findings get compressed at each handoff, and "keep going until dry" becomes "keep going until it feels
done". The script removes all three.

**Invoking this skill is the Workflow opt-in.** No further authorization is needed — but say what you
are running and roughly what it will cost before you launch it.

## How to run it

Call the Workflow tool with `name: "verify-loop"` and args:

```
{
  artifact:     "path/to/the/thing/under/test",     // required
  groundTruth:  ["path/a", "path/b"],               // what it must be checked AGAINST, not trusted about
  priorRounds:  ["path/to/earlier-verification.md"],// so findings are not re-reported
  angles:       ["completeness", "fail-open"],      // optional; the planner picks otherwise
  dryOutRounds: 2,                                  // consecutive empty rounds required to stop
  maxRounds:    4
}
```

`groundTruth` is the load-bearing argument. Without it the verifiers can only check the artifact
against itself, which is the failure this skill exists to prevent. If you cannot supply it, say so —
the workflow will report reduced confidence rather than fake it.

## What the workflow does

| Phase | What runs |
|---|---|
| **Plan** | One agent reads the artifact and prior rounds, picks 2–5 lenses that fail *differently*, and lists angles prior rounds proved dry so they are not re-run. |
| **Verify** | One agent per lens, in parallel, refute-by-default, each returning findings + a liveness statement + dead ends + an explicit unverified list. |
| **Adjudicate** | Two independent refuters per finding, with different angles — one assumes it does not reproduce, one assumes it is real but its stated cause is wrong. Majority refutation drops it. |
| **Report** | Confirmed findings, dead-end ledger, unverified items, and a dry-out verdict. |

Rounds repeat until `dryOutRounds` consecutive rounds produce nothing new, or the ceiling is hit —
in which case the report says so plainly rather than implying completion.

## The rules the script encodes

- **Evidence is quoted real text or executed output.** A paraphrase is not evidence. Prefer executing
  over reading whenever a claim is testable — in practice the execution lens finds the most.
- **An empty result must be proven, not assumed.** Every lens returns a liveness statement saying what
  was actually read or run. "I found nothing" without it is indistinguishable from "I looked nowhere".
- **Anything unchecked is reported as unverified,** never silently passed.
- **`silentLoss` is flagged separately** — a finding that would drop a rule if the artifact were acted
  on as written outranks ordinary severity.
- **Dead ends are recorded at class level**: "X failed BECAUSE Y", with the cousin cases that are still
  reachable. A dead end that only prevents re-walking one exact path is nearly worthless.
- **Dry-out, not a count.** Stopping after N findings measures your patience; stopping after N empty
  rounds measures the artifact.

## Anti-patterns

| Anti-pattern | The tell | Rule |
|---|---|---|
| **Gate that cannot fail** | The check has never denied anything | Every gate ships with a negative test proving it denies what it should |
| **Missing liveness assertion** | A scanner reports success on a renamed target | Every scanner asserts it found *something* |
| **Oracle leakage** | The harness hands the thing under test a guaranteed win | Verify the verifier before trusting a number it produced |
| **Refuting the reason, not the finding** | "Its explanation was wrong, so it's fine" | Re-derive the finding independently; a wrong cause does not clear a real defect |
| **Fix that reopens the bug** | A patch that was never run against the original failing case | Every proposed fix passes its own negative control |
| **Agreeableness** | The verifier confirms everything | A pass with no findings and no liveness statement is not a pass |
| **Metric blindness** | Only aggregates were read | Read the actual output, not just the summary |
| **Fabricated completion** | A result no one observed being produced | No record, no result — untested is a legal state, invented is not |

## Verdicts and what follows

- **Confirmed criticals or any `silentLoss`** → do not declare the work done. Fix, then re-verify.
- **Dry-out not reached** → say so in your report to the user, with the angle the next round should
  take. Do not round up to "verified".
- **Genuine judgment calls** → batch as NEEDS-RULING for the user rather than blocking or guessing.
  Abstention is a correct output; a confident wrong answer is not.

## When a workflow is overkill

For a single small artifact with one obvious failure mode, run one independent check inline and say
plainly that it was one check, not this protocol. Do not describe inline spot-checking as having run
`verify-work` — the name should mean the workflow ran.
