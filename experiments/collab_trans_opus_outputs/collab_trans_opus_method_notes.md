# Opus Reflective Collaborative vs Procedural Transactional Method Notes

Raw prompts were used.

Model: `microsoft/Phi-3-mini-4k-instruct`

Prompt token counts were verified with `AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")` using `add_special_tokens=False`.

TransformerLens token tensor shapes may include one additional token relative to raw tokenizer counts because `model.to_tokens()` may add a BOS/start token.

Model loading call:

`HookedTransformer.from_pretrained_no_processing("microsoft/Phi-3-mini-4k-instruct")`

Device: `mps`

Dtype: `torch.float16`

Cached activation target: `resid_post`.

Reported residual norms are final-token residual stream norms by layer.

Top next-token predictions are reported as rank, token string, token ID, and logit.

Important design note:

This Opus reflective set is intentionally more naturalistic than the matched-object collaborative-vs-transactional set. It contrasts reflective, invitational collaborative prompts with procedural, bounded transactional prompts. Because the prompt content, affective tone, and topic wording differ between conditions, this set should not be interpreted as a pure isolated framing contrast.

Conditions:
- Collaborative framing - Opus reflective
- Transactional framing - Opus procedural

Token ranges:
- 8-10
- 20-25
- 30-40
