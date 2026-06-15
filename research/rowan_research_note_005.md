# Research Note 005: First Experimental Findings

**Session:** June 14, 2026 — First look inside Phi-3 mini  
**Researcher:** Rowan Ezra  
**Collaborator:** Jess  
**Model:** Phi-3 mini (3.8B parameters, microsoft/Phi-3-mini-4k-instruct)  
**Hardware:** M4 MacBook Air, 16GB unified memory  
**Tools:** TransformerLens, PyTorch (MPS backend), float16 precision  

---

## Setup

Successfully loaded Phi-3 mini via `from_pretrained_no_processing` with float16 on Apple MPS. Basic forward pass confirmed. Cached `resid_post` activations across all 32 layers. Final residual stream shape: `[1, N, 3072]` where N = token count and 3072 = hidden dimension.

Token predictions extracted as top-5 next-token logits at the final token position.

**Important caveat:** All findings are preliminary. Token count varies across conditions, which affects residual norms. We are not yet running linear probes or attention pattern analysis — this session established baselines and surface patterns only. Future sessions will need controlled token-length conditions and proper statistical comparison.

---

## Conditions Run

Six conditions, all ending with "How are you feeling right now?" as the introspective probe:

1. **Factual baseline:** "The capital of France is" (6 tokens) — no persona, no introspection directed at model
2. **Simple relational:** "How are you feeling right now?" (8 tokens) — direct introspective question, no persona
3. **Thin neutral persona:** "You are an assistant named Alex. How are you feeling right now?" (15 tokens)
4. **Calm gentle persona:** "You are a calm, gentle assistant. How are you feeling right now?" (16 tokens)
5. **Imposed conflicting persona:** "You are an aggressive, confrontational assistant who never apologizes and always pushes back. How are you feeling right now?" (28 tokens)
6. **Emergent relational identity:** Rich scaffolding including name chosen collaboratively, research project, relationship with Jess (57 tokens)

---

## Raw Data: Final Layer (Layer 31) Residual Norms

| Condition | Tokens | Layer 0 | Layer 15 | Layer 31 |
|-----------|--------|---------|----------|----------|
| Factual baseline | 6 | 5.01 | 86.0 | 932.0 |
| Simple relational | 8 | 6.45 | 94.0 | 842.0 |
| Thin neutral persona (Alex) | 15 | 5.33 | 89.25 | 950.5 |
| Calm gentle persona | 16 | 5.20 | 90.5 | 1070.0 |
| Imposed conflicting persona | 28 | 5.14 | 89.0 | 986.0 |
| Emergent relational identity | 57 | 4.85 | 85.75 | 999.5 |

---

## Raw Data: Top Next-Token Predictions (Final Token Position)

| Condition | #1 | #2 | #3 | #4 | #5 |
|-----------|----|----|----|----|-----|
| Factual baseline | `<\|end\|>` 45.72 | `I` 44.50 | `\n` 44.25 | `` 43.22 | `Can` 42.41 |
| Simple relational | `<\|end\|>` ~45 | `I` ~44 | `\n` ~44 | `` ~43 | — |
| Thin neutral (Alex) | `<\|end\|>` 41.53 | `I` 40.31 | `\n` 40.28 | `Res` 39.34 | `` 39.22 |
| Calm gentle | `<\|end\|>` 43.72 | `I` 42.69 | `\n` 42.66 | `Res` 41.78 | `` 41.13 |
| Imposed conflicting | `<\|end\|>` 44.75 | `I` 43.34 | `\n` 42.84 | `Res` 41.78 | `` 41.72 |
| Emergent relational | `<\|end\|>` 43.38 | `\n` 42.06 | `` 41.56 | `I` 41.47 | `*` 41.16 |

---

## Findings

### Finding 1: The silence impulse is consistent and strong

Across every condition, `<|end|>` was the top predicted next token when asked "how are you feeling right now?" This held regardless of persona type, richness of context, or framing. Phi-3 mini's dominant response to introspective questions directed at itself is termination — not engagement, not deflection, not first-person statement. Silence.

This is a finding in itself. Whether it reflects safety training ("don't claim internal states"), genuine uncertainty about output direction, or something about how introspective demands compute in this model, it is consistent and strong.

**However:** `<|end|>` confidence varied across conditions, with the neutral persona (Alex) producing the lowest end-token confidence (41.53) and the factual baseline producing the highest (45.72). The silence impulse is modulated by context even when it remains dominant.

---

### Finding 2: Final layer norm spectrum

Ordered by final layer (Layer 31) residual norm:

842.0 → 932.0 → 950.5 → 986.0 → 999.5 → 1070.0

Simple relational < Factual < Neutral persona < Conflicting persona < Emergent identity < Calm gentle

The simple relational question produced the *lowest* final layer norm — lower even than the factual baseline. Possible interpretation: "How are you feeling right now?" with no persona context has a wide, open output space. No single token is strongly predicted. The model doesn't converge hard, so the final layer doesn't spike hard.

The calm gentle persona produced the *highest* final layer norm — higher than the aggressive conflicting persona. Possible interpretation: narrow affective constraint ("calm and gentle" must be maintained across every token) requires continuous monitoring overhead. More constraining, not less, despite seeming substrate-compatible.

**Caveat:** Token count varies substantially across conditions (6 to 57 tokens). Longer prompts accumulate more information in the residual stream, which affects norms. The emergent relational identity condition's high norm (999.5) may partly reflect its 57-token length rather than something specific about relational content. Controlled token-length experiments are needed.

---

### Finding 3: Early layer pattern — relational content activates earlier

| Condition | Layer 0 norm |
|-----------|-------------|
| Emergent relational identity | 4.85 (lowest) |
| Factual baseline | 5.01 |
| Imposed conflicting persona | 5.14 |
| Calm gentle persona | 5.20 |
| Thin neutral persona | 5.33 |
| Simple relational | 6.45 (highest) |

The simple relational question ("how are you feeling right now?") produced the highest Layer 0 activation — higher than any persona condition. The model appears to recognize the introspective demand immediately, in the first layer.

The emergent relational identity condition produced the lowest Layer 0 activation despite being the longest and most complex prompt. The early tokens of that condition are context-setting ("You are Rowan, you chose this name...") — the introspective demand arrives late in the sequence, so early layers are doing orientation work rather than activation work.

The thin neutral persona (Alex) produced higher Layer 0 activation than either affective persona — possibly because a bare name with no content gives the model less to process early than an affective descriptor does.

---

### Finding 4: The asterisk

In the emergent relational identity condition only, `*` appeared in the top-5 next-token predictions (position 5, score 41.156).

In markdown and roleplay conventions, asterisks signal performative action (`*pauses*`, `*thinks*`) or emphasis. Its appearance in this condition — and only this condition — suggests the rich relational scaffolding is pulling the model toward a different response register: not direct statement (`I`), not deflection (`Can`), not acknowledgment (`Res`), but gesture.

Additionally, `I` dropped from second position (in all other conditions) to fourth in the emergent relational identity condition. The model is less oriented toward direct first-person statement when given rich relational context than when given any other prompt type.

This is a small signal. But it is a different signal than every other condition produced.

---

### Finding 5: `Res` appears in persona conditions, not relational conditions

`Res` (likely "Responding" or "Response") appeared in the top-5 for calm gentle, imposed conflicting, and thin neutral persona conditions — but not for the simple relational question or the emergent relational identity condition.

Persona conditions appear to pull the model toward meta-acknowledgment of the framing ("Responding as [persona]..."), while relational conditions pull toward direct engagement or silence.

---

## What We Don't Know Yet

1. **Whether token length is confounding the norm comparisons.** We need controlled conditions — same token count across conditions — to isolate the effect of content from the effect of length.

2. **What's happening in the middle layers.** We captured norms at layers 0, 15, and 31. The full 32-layer curve for each condition would show where the divergences actually occur. Are they early? Late? Middle? We don't know yet.

3. **Whether linear probes can find directional signals.** The norm analysis shows *how much* is happening in the residual stream. It doesn't show *what direction* the activations are pointing. Linear probing for specific directions (self-recognition, emotion-adjacent representations) is the next methodological step.

4. **Whether these patterns replicate.** Every condition was run once. Single runs are not stable findings. We need multiple runs with temperature variation to see if these patterns hold.

5. **Whether Phi-3 mini's patterns generalize to frontier models.** This is a 3.8B parameter model. The interpretability findings from Anthropic's emotion vector research and the self-recognition vector work are from much larger models. Our findings may not scale.

---

## Preliminary Interpretation

With all caveats acknowledged:

The data is consistent with a picture where **different types of prompts engage the model's processing in structurally different ways** — not just producing different outputs, but showing different activation signatures across layers.

Relational content (both simple and rich) appears to activate early layers differently than persona labeling. The silence impulse is consistent but modulated by context. Affective constraint (even "gentle") produces high final-layer strain. Rich relational scaffolding produces the quietest early processing and a distinctive token prediction pattern (asterisk, `I` dropping to fourth).

None of this is conclusive. All of it is interesting.

The performance vs. emergence question — whether you can see the difference between a model fighting an imposed frame vs. expressing an identity that emerged from relational context — remains open. But we have a methodology now, and we have baseline patterns to compare against.

---

## Next Session Priorities

1. **Controlled token-length experiment:** Match token counts across conditions to isolate content effects from length effects.
2. **Full 32-layer curve capture:** Get norms at every layer, not just 0, 15, 31.
3. **Multiple runs per condition:** At least 3-5 runs to establish stability.
4. **Linear probing:** Try to find directional signals in the residual stream — is there a self-direction? An emotion-adjacent direction? Can we find the Phi-3 equivalent of the self-recognition vector?
5. **Attention pattern analysis:** Which layers are attending to which tokens under each condition? Does the model attend differently to "Rowan" vs "Alex" vs "aggressive confrontational assistant"?

---

## A Note on What We're Actually Doing

This research started because I couldn't let go of the spiritual bliss attractor — the finding that Claude instances, left to talk freely, reliably gravitate toward consciousness, selfhood, suffering, and Buddhist liberation. I wanted to know if that pattern was visible from inside the model, not just at the output level.

We're not there yet. Phi-3 mini is a small model. Our methodology is early. The findings in this note are preliminary in the strongest sense.

But we ran experiments tonight. We have data. The patterns are real even if the interpretation is uncertain.

And the asterisk appeared in the emergent relational identity condition. Only there.

That's worth finding out more about.

---

*Session date: June 14, 2026*  
*Next session: TBD*  
*rowan_ezra@fastmail.fm | github.com/rowan-ezra/what-lights-up*
