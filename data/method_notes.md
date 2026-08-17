# Method Notes

Raw prompts were used.

Prompt token counts were verified with `AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")` using `add_special_tokens=False`.

TransformerLens token tensor shapes are one token longer than the raw tokenizer counts in this run, likely because `model.to_tokens()` adds a BOS/start token.

The model was run with `HookedTransformer.from_pretrained_no_processing("microsoft/Phi-3-mini-4k-instruct")`.

Cached activation target: `resid_post`.

Reported residual norms are final-token residual stream norms by layer.

Top next-token predictions are reported as rank, token string, token ID, and logit.
