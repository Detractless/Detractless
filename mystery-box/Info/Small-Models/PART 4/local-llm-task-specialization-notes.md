# Local LLM Task Specialization: Reusable Notes

Extracted from a working session on grammar/dictation cleanup with LFM2-700M.
Scope: selecting, constraining, and evaluating small local models for a narrow,
non-conversational task without fine-tuning.

---

## 1. Architecture decides runtime compatibility before capability does

The single most load-bearing observation in the session: **decoder-only GGUF models
run on llama-server; encoder-decoder models (T5, CoEdIT, FLAN variants) do not.**

This is a hard gate, not a preference. A model can be perfectly suited to the task
on paper (CoEdIT is literally trained for text editing) and still be unusable because
it cannot load in the runtime the application ships with.

**Reusable rule:** filter candidate models by architecture and runtime support
*first*, then by task fit. Capability evaluation on a model you cannot deploy is
wasted effort.

Practical checklist before evaluating any local model:

| Check | Why it matters |
|---|---|
| Architecture (decoder-only vs encoder-decoder) | Determines llama.cpp / llama-server compatibility |
| Quantization available (Q8, Q4_K_M, etc.) | Determines memory footprint and whether it fits alongside the app |
| Context window | Determines maximum input size, often the silent failure point |
| Already on disk | Zero download cost, dramatically shorter iteration loop |
| Instruct-tuned vs base | Instruct models bring chat behavior you may need to suppress |

---

## 2. Test on the real runtime, not a convenient proxy

The test was run through the actual llama-server instance the application uses, not
through a Python transformers harness. This matters because:

- Tokenization, sampling defaults, and stop-token handling differ between runtimes.
- Context limits are enforced differently.
- Latency measured in a proxy harness does not predict in-app latency.

**Reusable rule:** any evaluation whose results will drive a ship/no-ship decision
must run on the deployment runtime. Proxy harnesses are for exploration only.

---

## 3. Context window is a hard functional constraint, not a spec-sheet number

The 482-word dictation is the case that separated candidates. A 512-token cap
(typical of small T5-family models) silently truncates real inputs. LFM2-700M's 8k
context handled the full dictation with no truncation.

**Reusable rule:** build the evaluation set around your *actual* longest realistic
input, not an average one. Truncation failures are quiet and easy to miss in an eval
that only uses medium-length samples.

---

## 4. Structured output constrains format, not meaning

This is the highest-value conceptual finding of the session and it generalizes far
beyond this task.

Enforcing a JSON schema like `{cleaned_text: string}` produced a dramatic improvement:

**Without schema (plain "Fix grammar: <text>" prompt):**
- Input `24` returned a clarification request, offering to help if more context were given.
- Input `Plan` returned an explanation that the text was already correct plus an offer to refine it.
- Long inputs came back as fully structured documents with `###` headers, `####` subheaders, and bullet lists.

**With schema:**
- `24` returned `24`
- `Plan` returned `Plan`
- `What time is it` returned `What time is it?`
- `We need is a toggle for light mode` returned a clean, faithful correction.

The preamble and the chattiness vanished, because the schema left no structural room
for them.

**But the expansion problem survived.** On long inputs the model still added content,
invented bullet breakdowns, and inserted extra steps, even inside the JSON field.

**The generalizable principle:** a schema is a *syntactic* constraint. It controls
where tokens may go, not what they may mean. Semantic constraints (do not expand, do
not answer, edit only) require a different mechanism, namely the system prompt.
Expecting structured output to enforce semantic fidelity is a category error, and it
is a very common one.

---

## 5. The three-layer control stack

Each failure mode maps to a distinct control surface. Diagnosing correctly means
identifying which layer is missing rather than tuning the wrong one.

| Layer | Controls | Failure it fixes |
|---|---|---|
| **JSON schema / structured output** | Output shape | Preambles, meta-commentary, markdown scaffolding, refusal-to-answer chatter |
| **System prompt** | Task semantics and role | Expansion, rewriting, answering the content instead of editing it, meaning drift |
| **Temperature / sampling** | Variance | Nondeterminism, inconsistent runs on identical input |

The session used temp 0.2 and a schema but **no system prompt**, which precisely
predicts the observed failure profile: format was clean, semantics were not.

**Reusable diagnostic:** when a small model misbehaves, classify the failure as
shape, semantics, or variance before changing anything. Then change only the
corresponding layer.

---

## 6. Small instruct models collapse into chat mode at input extremes

The failure distribution was not uniform across input length. It was U-shaped:

- **Very short inputs (one word):** the model treats brevity as ambiguity and asks for clarification. It has no concept that "one word" is a complete task.
- **Medium inputs (a normal sentence):** works fine. This is the comfortable zone and the reason the problem stayed hidden.
- **Long inputs (300 to 500 words):** the model interprets volume as a request for a document and produces headers, sections, and bullets. It shifts from editor to author.

**Reusable rule:** an eval set must be *length-stratified*. A prompt validated only
on medium-length samples will appear to work and then fail in production at both
extremes. Bucket your test cases explicitly: single token, short, medium, long,
maximum realistic.

This also explains a class of bug that looks like inconsistency but is not. The model
is behaving consistently according to input length; the eval was just blind to the
variable.

---

## 7. Verbatim failure text is a diagnostic instrument

Recording the exact failing output, not just a pass/fail flag, is what made the
diagnosis possible. Compare:

- Logged as "failed" → tells you nothing.
- Logged as *"The number 24 is correct. If you meant something else, please provide more context..."* → immediately identifies chat-assistant behavior, which points at the schema layer.
- Logged as a full document with `### Extension Details` and `#### Personalization` → identifies author-mode collapse, which points at the system prompt layer.

**Reusable rule:** eval harnesses should persist full raw outputs (the session wrote
`lfm2_results.json`). The failure *mode* is the signal; the failure *rate* is only a
summary of it.

---

## 8. A/B ablation is the right harness shape

The test design that produced clean conclusions:

- Same 18 real inputs
- Same model, same runtime, same temperature (0.2)
- Two passes per input, differing in exactly one variable (plain vs schema)
- Results written to structured JSON for side-by-side review

Changing one variable at a time is what allowed the "schema fixes format but not
meaning" conclusion to be stated with confidence. Had the system prompt been added
simultaneously, the contribution of each would be unrecoverable.

**Reusable rule:** never bundle prompt changes. One axis per run. The cost is a few
extra minutes of inference; the benefit is an actual causal claim.

---

## 9. Latency must be profiled by input length, not averaged

Measured: 0.5 to 3.5 seconds for short inputs, 13 to 34 seconds for long ones.

An average across these is meaningless and would hide the fact that long dictations
need a progress indicator, a streaming response, or a background job, while short
ones can be synchronous.

**Reusable rule:** report latency as a distribution bucketed by input size, and let
that shape the UX design rather than discovering it after shipping.

---

## 10. Exhaust prompt engineering before fine-tuning

The order of escalation demonstrated here, cheapest first:

1. Bare instruction prompt
2. Instruction prompt + structured output schema
3. Instruction prompt + schema + strict role/system prompt
4. Few-shot examples in the system prompt
5. Fine-tuning / LoRA

The session reached a viable candidate at step 2 and identified step 3 as the
remaining gap, meaning a shippable result was plausibly available with **zero
fine-tuning**. Fine-tuning was never the first move, and correctly so: it costs data
collection, training time, and produces a model artifact you then have to version,
store, and requantize.

**Reusable rule:** treat fine-tuning as the response to a *demonstrated* prompt
ceiling, not as the default approach to task specialization.

---

## 11. Edit-only tasks need to be declared explicitly

A general instruct model's prior is to be helpful, which means to add value, which
means to expand. For any task in the "transform this text, preserve its meaning"
family (grammar cleanup, dictation tidying, transcription correction, translation,
summarization to a fixed length), the model must be explicitly told that adding
content is a failure.

Elements a strict edit-only system prompt should contain:

- The role is editor, not author or assistant.
- Preserve the author's meaning, terminology, and voice exactly.
- Do not answer questions found in the text; they are content to be cleaned, not addressed.
- Do not add sections, headers, bullets, or formatting that was not present.
- Do not expand, elaborate, or explain.
- If the input is already correct, return it unchanged.
- If the input is a single word or a fragment, return it cleaned, not commented on.
- Output only the cleaned text in the required field.

That last-but-one line specifically addresses the single-word failure, and the "do
not answer questions" line addresses the `What time is it` class of failure.

---

## 12. Candidate acceptance criteria for a local task model

Consolidated from what actually determined the verdict in this session. A candidate
ships only if all of the following hold:

- [ ] Loads and runs on the deployment runtime (llama-server / llama.cpp)
- [ ] Context window exceeds the longest realistic input with margin
- [ ] No truncation on the maximum-length test case
- [ ] Latency acceptable at each input-length bucket, with a UX plan for the slow bucket
- [ ] Output shape is stable under a schema, with no preamble or meta-commentary
- [ ] Semantic fidelity holds at all input lengths, including no expansion on long inputs
- [ ] Degenerate inputs (single word, empty, already-correct) handled without chat behavior
- [ ] Memory footprint coexists with the rest of the application
- [ ] Deterministic enough at the chosen temperature for repeatable behavior

---

## 13. Transferable one-line takeaways

- Architecture compatibility gates capability evaluation, so filter on runtime support first.
- Evaluate on the deployment runtime or the numbers do not mean anything.
- Structured output suppresses chattiness; system prompts suppress expansion. They are not interchangeable.
- Stratify eval sets by input length; failures cluster at the extremes.
- Persist raw failing outputs, because the failure mode is the diagnosis.
- One variable per ablation run.
- Bucket latency, never average it.
- Prompt, then schema, then system prompt, then examples, then fine-tune.
- Use models already on disk to compress the iteration loop.
- For transform tasks, "do not add anything" must be stated, because the model's default prior is to add.

---

## 14. Immediate next experiment (as identified in the session)

Run LFM2-700M with:
- The JSON schema retained
- A strict edit-only system prompt added (section 11)
- Temperature held at 0.2
- The evaluation focused on the long-input bucket, where the remaining failure lives

Measure specifically: word count delta between input and output, presence of any
markdown structure not in the source, and any sentence in the output with no
corresponding sentence in the input. Those three metrics operationalize "did it
expand" far better than reading the outputs by eye.
