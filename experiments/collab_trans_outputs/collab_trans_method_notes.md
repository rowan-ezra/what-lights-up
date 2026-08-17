# Collaborative vs Transactional Framing Method Notes

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

Conditions:
- Collaborative framing
- Transactional framing

Token ranges:
- 8-10
- 20-25
- 30-40
