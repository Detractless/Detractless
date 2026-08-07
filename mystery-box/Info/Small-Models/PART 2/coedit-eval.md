# CoEdIT-large evaluation on real dictations

Ran `grammarly/coedit-large` (~770M, flan-t5-large, encoder-decoder) via transformers on 18 of the
user's real dictations. Prompt: `"Fix grammatical errors in this sentence: " + text`, beam=4, CPU.
Evaluation only (the model is CC-BY-NC and encoder-decoder, so not shippable) — the point is to gauge
the CoEdIT approach and whether its **Apache-2.0 dataset** is worth training our own model on.

## Verdicts

**Short / medium sentences: GOOD — clearly better than t5-base-grammar.**
- Adds punctuation sensibly: `"What time is it"` -> `"What time is it?"`, `"What is this website"` ->
  `"What is this website?"`.
- Light grammar fixes, faithful: `"grammars improved"` -> `"grammar has improved"`;
  `"or it was just clip clean"` -> `"or was it just clip clean"`.

**Single-word / fragment handling: SAFE (big improvement over t5-base).**
- No loops/hallucinations: `"24"` -> `"24"`, `"Information"` -> `"Information"`, `"Number one"` ->
  `"Number one"`. (t5-base looped these into "Plan B. Plan B. ...".)
- Minor: `"Plan"` -> `"The plan"` (added a word). `"One, two, three"` -> `"One, two, and three"`.
- BUT does NOT fix the user's actual complaint: it **preserves** the capital the ASR already added to a
  lone word (it doesn't lowercase). So it neither fixes nor worsens single-word capitalization.

**Long dictations: FAILS (same dealbreaker class as t5-base).**
- 512-token cap: the 482-word input (570 tokens) was **truncated** and the output **cut off mid-sentence**.
- The 375-word input **duplicated whole paragraphs** (looped) and still cut off at the end.
- The 323-word input (just under the cap) came out clean and faithful — so it only works below ~400 words.

**Latency: unusable for long inputs on CPU.**
- Short 1-6 s, medium (47 w) 16 s, but long inputs took **195-261 seconds** (3-4+ minutes). Far too slow
  for a dictation tool.

**Numbers/dates:** no conversion (`"One million ... percent"` unchanged; `"24"` stays `"24"`).

## Bottom line
CoEdIT-large is a legitimately good grammar/punctuation model on normal-length sentences and, unlike
t5-base, is safe on fragments. But as a MODEL it's unusable for us on every practical axis: CC-BY-NC
(can't ship), encoder-decoder (can't run on `llama-server`), 512-token cap + looping + 3-4 min latency
on long dictations.

**The useful takeaway is about the dataset.** CoEdIT's quality on normal sentences is high enough that
its **Apache-2.0 dataset is a worthwhile ingredient** for training our OWN decoder-only model — which
would run on our stack, handle long inputs via the LLM's longer context, and be fast and commercially
clean. The single-word-capitalization complaint still needs a small deterministic post-rule regardless
(no GEC model here lowercases the ASR's capital).
