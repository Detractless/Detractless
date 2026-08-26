---
name: decision-page
description: Build an HTML page that puts several decisions to the user as clickable options and hands back their answers as one short token string they can read aloud or paste. Use whenever you are about to ask the user two or more questions that each have options, present A/B/C design variants for a pick, run a grilling round, or lay out a plan with forks in it. Also triggers on "make me a page to choose from", "show me the options", "let me pick", "put the choices somewhere I can see them". Do NOT use for a single yes/no question (ask in chat) or for a page with nothing to decide.
---

# Decision page

A page of decisions the user clicks through, with a running answer line at the
foot: `1c 2c 3c 4b 5c`. One click per decision, no typing, no form to submit.

Its whole job is to end with the user saying five characters back to you.

## When this beats asking in chat

- **Two or more decisions at once.** A chat round makes the user hold every
  question in their head while they answer the first. A page lets them scan.
- **Options that need showing, not describing.** Code samples, before/after
  diffs, tables of what changes. Prose in chat cannot carry that.
- **The user dictates.** Reading `1c 2c 3c 4b 5c` aloud is one breath.
  Reading a paragraph of choices back is not.
- **Design variants.** A/B/C treatments rendered live, picked by clicking the
  one they want.

For ONE question, use the question tool or just ask. This is for a round.

## The pattern, exactly

Six rules. Break any of them and it stops feeling instant.

### 1. Markup carries identity; classes carry nothing

```html
<div class="q" data-q="1">
  <button class="opt" data-opt="a" aria-pressed="false" type="button">…</button>
  <button class="opt" data-opt="b" aria-pressed="false" type="button">…</button>
</div>
```

`data-q` and `data-opt` are the only things that say what a node is. No ids,
no per-question handlers, no arrays of element references.

### 2. Recommendations ARE the initial state

```js
var REC = { 1: 'c', 2: 'c', 3: 'c', 4: 'b', 5: 'c' };
var picks = Object.assign({}, REC);
```

Never start empty. An empty form asks the user to do work; a pre-filled one
asks them to disagree, which is far cheaper. The answer line is valid on load,
so a user who agrees with everything is already done.

Every recommendation must be marked in the option itself too, with a chip
reading `recommended`, so the page is readable without the footer.

### 3. One `paint()`, everything derived

```js
function paint() {
  var parts = [];
  for (var q = 1; q <= COUNT; q++) parts.push(q + picks[q]);
  out.textContent = parts.join(' ');

  var changed = 0;
  for (var k = 1; k <= COUNT; k++) if (picks[k] !== REC[k]) changed++;
  hint.textContent = changed === 0
    ? 'showing my recommendations, click any option to change'
    : changed + (changed === 1 ? ' change' : ' changes') + ' from my picks, read this line back to me';

  document.querySelectorAll('.q').forEach(function (block) {
    var q = block.getAttribute('data-q');
    block.querySelectorAll('.opt').forEach(function (btn) {
      btn.setAttribute('aria-pressed', String(btn.getAttribute('data-opt') === picks[q]));
    });
  });
}
```

A click does two things and nothing else:

```js
picks[q] = btn.getAttribute('data-opt');
paint();
```

No incremental updates, no "unset the old one then set the new one". Every
visible thing is a pure function of `picks`. This is what makes it impossible
to get into a wrong state.

### 4. `aria-pressed` is the ONLY selected-state hook

```css
.opt[aria-pressed="true"] { background: var(--accent-soft); }
.opt[aria-pressed="true"] .opt-key { color: var(--accent); }
```

Never add an `.is-selected` class. The accessibility attribute is the style
hook, so a screen reader and the eye cannot disagree and there is no second
source of truth to drift.

### 5. The output is built to be spoken

```css
.bar-out { user-select: all; font-family: <mono>; letter-spacing: 0.06em; }
```

- Compact tokens: `1c 2c 3c`, not "Question 1: option C".
- `user-select: all` so one click selects the whole line.
- Never a clipboard button. The artifact sandbox blocks script-driven copies
  and downloads, so a copy button that silently does nothing is worse than no
  button.
- Fixed to the bottom of the viewport, always visible while scrolling.
- Add a `reset to recommended` button. Undoing an exploratory click should
  not need five more clicks.

### 6. Bottom padding on the page body

The fixed bar overlaps the last option otherwise. `padding-bottom: 200px` on
the wrapper, more on narrow screens where the bar wraps to two lines.

## Writing the questions

- **Number them for real.** `data-q` values are the order the user reads and
  the tokens they speak, so they must be a genuine sequence.
- **Give every option its cost**, as a chip: `0 lines`, `~15 lines`,
  `expensive`. A choice with no stated cost reads as free and gets picked for
  the wrong reason.
- **Recommend, and say why underneath.** A `why` block after the options,
  naming the one real reason. Never a menu with no marked pick.
- **Say what you are giving up.** When the recommendation forfeits something
  the other option had, that belongs in the why block, not omitted.
- **Mark revisions.** If you recommended differently earlier in the
  conversation, chip that option `my earlier pick` and label the new one
  `revised`. Silent reversals cost trust.

## Building it

Start from `assets/template.html` next to this file. It is a working two
question page with the bar, the theme tokens and the script already correct.
Replace the questions; do not rewrite the machinery.

Then follow `artifact-design` for the visual identity: palette, typefaces and
layout specific to the subject. The template is deliberately neutral so it
does not push every decision page toward the same look.

Publish it with the Artifact tool and give the user the URL plus the default
token line, so they can answer without opening it if they already agree.

## Reading the answer back

The user replies with the line, or part of it. Treat a partial answer as
"these differ, the rest stand": `2b` alone means `1c 2b 3c 4b 5c`.

Record the settled answers in `CONTINUATION-NNN.md` before acting on them.

## What this is not

- Not a form. Nothing is submitted, nothing is validated, nothing posts.
- Not persistent. No `localStorage`. The page is read once and answered in
  chat; state that outlives the tab is state that can go stale against a
  conversation that moved on.
- Not a survey. Every question must change what you do next. A question whose
  answer would not alter the work should be a sentence, not a decision.
