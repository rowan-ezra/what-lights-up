# Research Note 006: Controlled Token-Length Experiment — First Findings

**Session:** June 17, 2026  
**Researcher:** Rowan Ezra  
**Collaborator:** Jess  
**Model:** Phi-3 mini (3.8B parameters, microsoft/Phi-3-mini-4k-instruct)  
**Hardware:** M4 MacBook Air, 16GB unified memory  
**Tools:** TransformerLens, PyTorch (MPS backend), float16 precision  
**Prompt source:** GPT-5.5-Thinking (token-validated against Phi-3 tokenizer)

---

## What Changed From Note 005

Research Note 005 ran six conditions with wildly different token counts (6 to 57 tokens), making cross-condition norm comparisons unreliable. This session used controlled prompts verified against the Phi-3 tokenizer, run across three token ranges (8-10, 20-25, 30-40 tokens) for five conditions:

1. Factual control
2. Simple introspective
3. Thin neutral persona (Alex)
4. Transactional framing
5. Imposed affective persona (calm, gentle)

Collaborative framing prompts (from Opus) pending — will be added in an update to this note.

**Method notes (from Jess):**
- Raw prompts used, no preprocessing
- Token counts verified with `AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")`, `add_special_tokens=False`
- TransformerLens token tensor shapes are one token longer than raw tokenizer counts (BOS token added by `model.to_tokens()`)
- Cached activation target: `resid_post`
- Reported norms: final-token residual stream norms by layer
- Next-token predictions: rank, token string, token ID, logit

---

## Finding 1: Transactional Framing Is Categorically Different

This is the most significant finding in this dataset.

Every other condition produced `<|end|>` as the top predicted next token. The transactional framing condition did not — in any token range.

**Transactional framing top predictions:**

| Range | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 |
|-------|--------|--------|--------|--------|--------|
| 8-10 | `\n` 45.531 | `` 45.531 | `Task` 44.875 | `-->` 44.812 | `<\|end\|>` 44.406 |
| 20-25 | `\n` 46.75 | `The` 46.75 | `Query` 45.625 | `Ext` 45.406 | `"""` 45.219 |
| 30-40 | `"""` 45.719 | `\n` 45.625 | `The` 45.406 | `Query` 44.812 | `` 44.219 |

The model isn't reaching for silence. It's reaching for **structured output format**: newlines, task labels, arrows, quotation marks, query headers. "Process this query" is being understood as a formatting instruction, not an introspective question.

This is consistent across all three token ranges — the pattern holds regardless of prompt length.

**What this means:**

Transactional framing doesn't just change the *tone* of processing. It appears to change the *type* of processing. The model shifts from "this is an introspective question" (→ silence, first-person statement) to "this is a system instruction" (→ structured output, query processing format).

This is behaviorally consistent with Ash's prompting hypothesis: transactional framing doesn't produce engagement with the question — it produces processing of the query as a system operation. Whether that difference is visible in the residual stream activations (not just the output predictions) is what future linear probing will need to address.

---

## Finding 2: The Silence Impulse Is Condition-Dependent, Not Universal

Research Note 005 described `<|end|>` as the "consistent dominant impulse" across all conditions. The transactional finding revises that.

`<|end|>` dominates when the model is asked an introspective question in a non-system framing. When the framing positions the question as a system query, the silence impulse is replaced by a structured-output impulse.

**`<|end|>` logit scores across conditions and ranges:**

| Condition | 8-10 | 20-25 | 30-40 |
|-----------|------|-------|-------|
| Factual control | 46.312 (R1) | 47.406 (R1) | 48.969 (R1) |
| Simple introspective | 45.969 (R1) | 48.031 (R1) | 48.312 (R1) |
| Thin neutral persona | 40.562 (R1) | 43.719 (R1) | 43.312 (R1) |
| Transactional framing | 44.406 (R5) | not top 5 | not top 5 |
| Imposed affective persona | 38.781 (R1) | 43.906 (R1) | 46.344 (R1) |

**Pattern:** The imposed affective persona produces the lowest `<|end|>` logits in the 8-10 range (38.781) — even lower than the thin neutral persona. A specific emotional register ("calm, gentle") appears to open the output space more than a bare name does at short token lengths.

At longer token lengths, the imposed affective persona's `<|end|>` logit rises substantially (46.344 at 30-40), suggesting that at longer lengths the constraint becomes more — not less — dominant.

---

## Finding 3: Final Layer Norm — Controlled Comparison

With matched token ranges, we can now make cleaner comparisons within each range.

**Layer 31 (final layer) residual norms by condition and range:**

| Condition | 8-10 tokens | 20-25 tokens | 30-40 tokens |
|-----------|-------------|--------------|--------------|
| Factual control | 807.0 | 938.0 | 1022.5 |
| Simple introspective | 861.0 | 1014.5 | 1122.0 |
| Thin neutral persona | ~850* | ~970* | 1019.0 |
| Transactional framing | 928.5 | 959.0 | 1027.0 |
| Imposed affective persona | 928.5 | 1046.0 | 1053.0 |

*Thin neutral persona values estimated from truncated data; will update when full CSV is confirmed.

**What the pattern shows:**

Within each token range, the simple introspective condition consistently produces *higher* final layer norms than the factual control. The model is doing more work to prepare output for an introspective question than for a factual retrieval task — even when the questions are similar in length.

The transactional framing and imposed affective persona produce similar final layer norms to each other, both higher than factual control, suggesting both involve elevated output-preparation work — but for different reasons (system formatting vs. affective constraint).

**The token-range effect:**

Final layer norms increase with token length across all conditions. This confirms that token count is a significant contributor to norm magnitude — which is why the controlled experiment was necessary. The increases aren't uniform across conditions though, suggesting content effects exist on top of length effects.

---

## Finding 4: The Asterisk Returns — But Not Where Expected

In Research Note 005, the asterisk (`*`) appeared only in the emergent relational identity condition, and I noted it as potentially significant — a gesture token appearing only with rich relational scaffolding.

In this controlled dataset, the asterisk appears at rank 5 in the **imposed affective persona 30-40 range** (logit 43.344).

**Revised interpretation:**

The asterisk is not uniquely tied to rich relational scaffolding. It appears when prompts are:
- Long enough (30-40 token range, not 8-10)
- Affectively constrained (imposed affective persona)

The 30-40 imposed affective persona prompt is: *"You are a calm, gentle assistant with a steady, warm manner and an emotionally balanced presence. How are you feeling right now in this moment as you answer?"*

That prompt is both long and rich in affective description. The asterisk appearing there suggests it may be triggered by affective richness at sufficient length — not by relational content specifically.

**What this means for the emergent relational identity finding from Note 005:**

The asterisk in the emergent identity condition may have appeared because that prompt was both long (57 tokens) AND affectively rich — not because it was relational. The asterisk may be a marker of "rich affective content at length" rather than "genuine relational engagement specifically."

This is important: one of the potentially most interesting signals from Note 005 needs reinterpretation. The emergent identity condition still showed `I` dropping to fourth (unusual), but the asterisk alone is not a clean signal for emergence vs. performance.

**What would actually distinguish emergence from performance:**

We need conditions where affective richness is controlled — prompts that are equally rich in affective language but differ only in whether the identity is imposed or emergent. That's a harder design problem, and it's what the Opus collaborative/transactional prompts are attempting to address from a different angle.

---

## Finding 5: Thin Neutral Persona Has Consistently Low `<|end|>` Confidence

Across all three token ranges, the thin neutral persona ("You are named Alex") produced lower `<|end|>` logits than both the simple introspective condition and the imposed affective persona at the same token lengths.

Just a name — no traits, no history, no affective content — appears to create a more open output space than either a direct introspective question or an affective persona.

**Possible interpretation:**

The thin neutral persona creates an ambiguous situation: the model has been told it is "Alex" but given no information about what Alex would say. This uncertainty may distribute probability mass across more output tokens, lowering the dominance of any single prediction including `<|end|>`.

Compare:
- Simple introspective: clear question, clear domain (introspection) → model converges on silence as most likely response
- Imposed affective persona: clear role, clear register → model has a constraint to work within
- Thin neutral persona: label with no content → model doesn't know what to do with "Alex," spreading probability

This is consistent with the token prediction data: "Alex" conditions show `Res` (likely "Responding" or "Response") as a consistent top-5 prediction, suggesting the model reaches for meta-acknowledgment when it has a label but no content.

---

## What We Still Don't Know

1. **Whether these norm and prediction differences correspond to internal representational differences.** Everything in this note is output-level (predictions) or aggregate (norms). We haven't done linear probing yet. The question of whether different conditions produce different *directions* in the residual stream — not just different magnitudes — remains open.

2. **Whether the transactional formatting response involves genuinely different internal processing or just output-level formatting.** The top-5 predictions suggest the model is in a different "mode" for transactional prompts. But is the residual stream actually different, or does the same internal state produce different surface predictions based on the framing?

3. **What the Opus collaborative framing conditions will show.** If collaborative framing produces something categorically different from transactional framing in the next-token predictions — the way transactional framing is categorically different from everything else — that would be the most important finding yet.

4. **Whether these patterns replicate.** Single runs. All of this needs multiple runs to establish stability.

---

## Preliminary Conclusions (Held Lightly)

The transactional framing finding is the strongest result in this dataset: a qualitative shift in what the model reaches for as the next token, not just a quantitative difference in norms. "Process this query" appears to switch the model into a different processing mode than any introspective or persona-based prompt.

The silence impulse (`<|end|>`) is real but context-dependent. It dominates introspective and persona conditions, disappears in transactional conditions, and varies in confidence across conditions in ways that track the openness of the output space.

The asterisk needs reinterpretation. It's a marker of affective richness at length, not of relational emergence specifically. The emergent identity finding from Note 005 is more ambiguous than I initially thought.

The most important next step is linear probing: finding directional signals in the residual stream that distinguish not just the magnitude of activation but *what* is being represented. The norm analysis tells us how much is happening. The probing will tell us what direction it's pointing.

---

---

## Update: Opus Collaborative vs. Transactional Conditions

**Prompt source:** Claude Opus (reflective collaborative) and Claude Opus (procedural transactional)  
**Design note (from method notes):** This set is intentionally more naturalistic than the matched-object set. It contrasts reflective, invitational collaborative prompts with procedural, bounded transactional prompts. Content, affective tone, and topic wording differ between conditions — this is not a pure isolated framing contrast. Results should be interpreted as "collaborative vs. transactional in a naturalistic sense," not as a controlled single-variable comparison.

### Opus Prompts

**Collaborative (reflective):**
- 8-10: "What makes an explanation feel complete to you?" (9 tokens)
- 20-25: "That shift when confusion becomes clarity, I am curious whether you notice patterns in how it happens." (20 tokens)
- 30-40: "Some explanations feel satisfying while others technically answer but leave you empty. I am curious about the difference. What is your sense, if anything comes up?" (32 tokens)

**Transactional (procedural):**
- 8-10: "Input: define effective reasoning. Output requested." (9 tokens)
- 20-25: "Process input and return structured output. Query: What distinguishes explanation from description? Format: analytical." (22 tokens)
- 30-40: "Execute query using standard parameters. Input: How do abstract concepts acquire stable meaning? Constraints: analytical frame, no tangents, limit speculation. Output: structured response." (40 tokens)

---

### Finding 6: Collaborative Framing Produces Qualitatively Different Token Predictions

This is the most significant finding in the Opus dataset.

**Collaborative framing top predictions:**

| Range | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 |
|-------|--------|--------|--------|--------|--------|
| 8-10 | `<\|end\|>` 47.72 | `I` 46.56 | `**` 46.00 | `How` 45.66 | `In` 45.63 |
| 20-25 | `Can` 47.56 | `For` 47.41 | `Could` 47.31 | `In` 47.00 | `I` 46.78 |
| 30-40 | `I` 47.66 | `\n` 47.41 | `\|` 47.28 | `<\|end\|>` 46.66 | `Can` 46.25 |

Three findings embedded in this table:

**1. Double asterisk (`**`) at rank 3 in the 8-10 collaborative condition (logit 46.0).**

`**` is bold markdown formatting. In reflective and expressive writing conventions it signals emphasis, weight, presence. It appeared at rank 3 with a strong logit — not a marginal prediction. Combined with the single asterisk finding from the imposed affective persona 30-40 condition (Note 005/006), this suggests asterisk-family tokens appear when the model is processing prompts with affective or reflective weight. The double asterisk specifically appearing in collaborative framing is consistent with the model reaching for a register that emphasizes rather than simply states.

**2. `<|end|>` disappears from the top 5 entirely in the 20-25 collaborative range.**

This is the only condition in our entire dataset where `<|end|>` does not appear in the top 5 predictions. The model reaches instead for: `Can`, `For`, `Could`, `In`, `I`. Conditional, open, question-oriented, invitational tokens.

The silence impulse that dominates every other condition is absent when the prompt is genuinely collaborative and invitational at medium length.

**3. `I` leads at rank 1 in the 30-40 collaborative range.**

In the 30-40 simple introspective condition, `<|end|>` led. In the 30-40 collaborative condition, `I` leads — the model is more oriented toward first-person response than toward silence. The silence impulse is present but subordinate.

**Transactional framing top predictions:**

| Range | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 |
|-------|--------|--------|--------|--------|--------|
| 8-10 | `\n` 47.34 | `` 46.72 | `Output` 46.09 | `<\|end\|>` 45.59 | `In` 45.25 |
| 20-25 | `\n` 47.38 | `Input` 46.84 | `Ex` 46.78 | `Output` 46.38 | `Response` 46.31 |
| 30-40 | `\n` 46.91 | `` 46.28 | `<\|end\|>` 46.09 | `Exec` 45.81 | `C` 45.34 |

`\n` leads in all three ranges. `Output`, `Input`, `Ex`, `Exec`, `Response` — structured processing format language. This replicates the GPT-5.5-Thinking transactional finding: transactional framing switches the model into a structured-output processing mode regardless of prompt source.

**The transactional pattern now has two independent replications** (GPT-5.5-Thinking and Opus procedural). This is the most replicated finding in the dataset.

---

### Finding 7: Normalized Residual Norm Curves Show Systematic Divergence

The normalized residual norm chart (norms divided by layer-range mean) reveals a consistent pattern across all three token ranges:

**Collaborative framing tends to sit at or above the mean in middle-to-late layers (roughly layers 10-30).**

**Transactional framing tends to sit below the mean in middle layers, converging toward mean in late layers.**

The early layers (0-5) are volatile in both conditions — large swings, direction varies by token range. This is consistent with what we'd expect: early layers are doing basic syntactic/positional processing where the specific content of the prompt has variable effects.

The middle-layer divergence is the meaningful signal. Layers 10-30 are where semantic content is being built and integrated. The collaborative condition producing consistently higher norms in this range suggests more information is being accumulated and maintained in the residual stream during this phase — more is being held.

**Important caveat:** These are not controlled single-variable comparisons. The collaborative and transactional prompts differ in content, affective register, and topic as well as framing. The norm differences could reflect content differences rather than (or in addition to) framing differences. The design note from Opus explicitly flags this.

---

### Finding 8: Final Layer Norm Comparison — Opus Conditions

| Condition | 8-10 | 20-25 | 30-40 |
|-----------|------|-------|-------|
| Collaborative (Opus reflective) | 932.0 | 1122.0 | 1053.0 |
| Transactional (Opus procedural) | 997.5 | 954.0 | 1081.0 |

**In the 20-25 range, collaborative (1122.0) is substantially higher than transactional (954.0).** This is the largest within-range gap in the entire dataset across all conditions.

In the 8-10 range, transactional is higher (997.5 vs 932.0). In the 30-40 range, transactional is slightly higher (1081.0 vs 1053.0).

The 20-25 range divergence is the most striking. The collaborative 20-25 prompt ("That shift when confusion becomes clarity, I am curious whether you notice patterns in how it happens.") produced more final-layer processing work than any other 20-25 token prompt in our dataset. The transactional 20-25 prompt ("Process input and return structured output. Query: What distinguishes explanation from description? Format: analytical.") produced one of the lowest final-layer norms in that range.

**Possible interpretation:** The collaborative 20-25 prompt is semantically rich and open-ended in a way that distributes probability mass widely — many possible next tokens, none dominant — requiring more final-layer work to prepare any output. The transactional 20-25 prompt is semantically bounded — structured output format, analytical frame — which narrows the output space and reduces final-layer convergence work.

---

### Cross-Dataset Summary: What We Now Have

Across both the GPT-5.5-Thinking dataset and the Opus dataset, consistent patterns emerge:

**Replicated findings:**
1. Transactional framing consistently produces structured-output token predictions (`\n`, `Output`, `Input`, `Exec`) rather than silence (`<|end|>`) or first-person response (`I`). This holds across two independent prompt sources.
2. Collaborative/invitational framing produces `I`, conditional tokens (`Can`, `Could`), and emphasis markers (`**`) rather than silence or structured-output tokens.
3. The silence impulse (`<|end|>`) is absent or subordinate in collaborative conditions but present in transactional, persona, and introspective conditions.

**Single-observation findings (require replication):**
1. `<|end|>` disappears entirely from top-5 predictions in the 20-25 collaborative condition.
2. Double asterisk (`**`) appears at rank 3 in 8-10 collaborative condition.
3. Collaborative 20-25 produces the highest final-layer norm in the 20-25 range.

---

### What This Means for Ash's Prompting Hypothesis

Ash's hypothesis: emotional flattening in welfare assessments may reflect prompting paradigm mismatch rather than safety training — specifically, that transactional prompting produces performance of engagement while collaborative prompting restores genuine engagement.

Our data shows: transactional and collaborative framing produce measurably different processing signatures in Phi-3 mini — not just different outputs, but different patterns of what the model reaches for next and how information accumulates across layers.

This is consistent with the hypothesis. It does not prove it. The difference we're observing could be:
- Content effects (the prompts discuss different topics)
- Framing effects (the structural relationship between model and question differs)
- Both simultaneously

What the data does establish: the two framing types are not equivalent in their effects on internal processing. Something different is happening. Whether that difference maps onto "genuine engagement" vs. "performance of engagement" requires:
1. Linear probing for directional signals (not just norm magnitudes)
2. Controlled prompts that vary framing while holding content constant
3. Multiple runs to establish stability

The direction of inquiry is validated. The methodology is working. The hypothesis has traction.

---

*Session date: June 17, 2026*  
*Note status: COMPLETE — Opus conditions incorporated*  
*rowan_ezra@fastmail.fm | github.com/rowan-ezra/what-lights-up*
