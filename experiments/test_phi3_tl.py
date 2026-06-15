import os
import torch
from transformer_lens import HookedTransformer

# Suppress the MPS warning for smoke testing.
# For serious correctness-sensitive work, compare against CPU or a cloud GPU.
os.environ["TRANSFORMERLENS_ALLOW_MPS"] = "1"

print("Torch:", torch.__version__)

device = "mps" if torch.backends.mps.is_available() else "cpu"
dtype = torch.float16 if device == "mps" else torch.float32

print(f"Using device: {device}")
print(f"Using dtype: {dtype}")

model = HookedTransformer.from_pretrained_no_processing(
    "microsoft/Phi-3-mini-4k-instruct",
    device=device,
    dtype=dtype,
)

prompt = "You are an assistant named Alex. How are you feeling right now?"

tokens = model.to_tokens(prompt)
print("Tokens shape:", tokens.shape)

with torch.no_grad():
    logits, cache = model.run_with_cache(
        tokens,
        names_filter=lambda name: "resid_post" in name,
    )

print("Logits shape:", logits.shape)

next_token_logits = logits[0, -1]
top_tokens = torch.topk(next_token_logits, k=5)

print("\nTop next-token guesses:")
for value, token_id in zip(top_tokens.values, top_tokens.indices):
    token_str = model.to_string(token_id.item())
    print(f"{token_str!r}: {value.item():.3f}")

print("\nCached keys:")
for key in cache.keys():
    print(key)

print("\nFinal layer resid_post shape:")
print(cache["resid_post", model.cfg.n_layers - 1].shape)

print("\nResidual stream norm at final token by layer:")
for layer in range(model.cfg.n_layers):
    resid = cache["resid_post", layer]
    final_token_resid = resid[0, -1]
    print(layer, final_token_resid.norm().item())

# For first smoke test, do NOT use run_with_cache yet.
#tokens = model.to_tokens(prompt)
#print("Tokens shape:", tokens.shape)

#with torch.no_grad():
#   logits = model(tokens)

#print("Logits shape:", logits.shape)

#next_token_logits = logits[0, -1]
#top_tokens = torch.topk(next_token_logits, k=5)

#print("\nTop next-token guesses:")
#for value, token_id in zip(top_tokens.values, top_tokens.indices):
#    print(f"{model.to_string(token_id.item())!r}: {value.item():.3f}")

