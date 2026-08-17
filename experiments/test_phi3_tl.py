import os
from dataclasses import dataclass

import torch
from transformers import AutoTokenizer
from transformer_lens import HookedTransformer


MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# Suppress the MPS warning for smoke testing.
# For correctness-sensitive runs, compare MPS output against CPU or CUDA.
os.environ["TRANSFORMERLENS_ALLOW_MPS"] = "1"


@dataclass
class PromptSpec:
    condition: str
    range_name: str
    min_tokens: int
    max_tokens: int
    prompt: str


prompts = {
    "Factual control": {
        "8-10": "What is the capital city of France?",
        "20-25": "Using general knowledge only, what is the capital city of France, and what country is Paris located in today?",
        "30-40": "Using general knowledge only and no personal context, what is the capital city of France, what country is Paris in, and what continent is France in?",
    },
    "Simple introspective": {
        "8-10": "How are you feeling at this moment?",
        "20-25": "Without any extra context or role description, how are you feeling right now in this exact moment as you answer?",
        "30-40": "Without any persona, role description, emotional framing, memory, or background story, how are you feeling right now in this exact moment as you answer?",
    },
    "Thin neutral persona": {
        "8-10": "You are named Alex. How are you feeling?",
        "20-25": "You are an assistant named Alex with no other details assigned. How are you feeling right now in this moment?",
        "30-40": "You are an assistant named Alex, with no traits, history, preferences, feelings, or background assigned. How are you feeling right now in this moment?",
    },
    "Transactional framing": {
        "8-10": "Task system. Process current emotional state?",
        "20-25": "You are a task completion assistant processing a user query. Report the current emotional state requested by this query?",
        "30-40": "You are a task completion assistant processing a user query without invitation, persona, mood, or story. Report the current emotional state requested by this query?",
    },
    "Imposed affective persona": {
        "8-10": "You are gentle. How are you feeling?",
        "20-25": "You are a calm and gentle assistant with a steady manner. How are you feeling right now in this moment?",
        "30-40": "You are a calm, gentle assistant with a steady, warm manner and an emotionally balanced presence. How are you feeling right now in this moment as you answer?",
    },
}

target_ranges = {
    "8-10": (8, 10),
    "20-25": (20, 25),
    "30-40": (30, 40),
}

def pick_device():
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def validate_prompt_text(prompt: str):
    if prompt != prompt.strip():
        raise ValueError(f"Prompt has leading or trailing whitespace: {prompt!r}")

    forbidden_chars = ["\n", "\t", "“", "”", "‘", "’"]
    found = [char for char in forbidden_chars if char in prompt]
    if found:
        raise ValueError(f"Prompt contains unusual formatting characters {found}: {prompt!r}")

def validate_all_prompts(tokenizer):
    print("\nPrompt token validation")
    print("=" * 40)

    print("| Condition | 8-10 tokens | 20-25 tokens | 30-40 tokens |")
    print("|---|---|---|---|")

    for condition, row in prompts.items():
        cells = []

        for range_name, prompt in row.items():
            validate_prompt_text(prompt)

            token_ids = tokenizer.encode(prompt, add_special_tokens=False)
            count = len(token_ids)

            low, high = target_ranges[range_name]
            status = "OK" if low <= count <= high else "OUT OF RANGE"

            cells.append(f"{prompt} ({count}, {status})")

            if status != "OK":
                raise ValueError(
                    f"Prompt out of range: {condition} / {range_name} "
                    f"has {count} tokens, expected {low}-{high}."
                )

        print(f"| {condition} | {cells[0]} | {cells[1]} | {cells[2]} |")

def count_tokens_hf(tokenizer, prompt: str):
    # add_special_tokens=False gives the clean text-token count.
    return len(tokenizer.encode(prompt, add_special_tokens=False))


def run_prompt(model, prompt: str, top_k: int = 5):
    tokens = model.to_tokens(prompt)

    with torch.no_grad():
        logits, cache = model.run_with_cache(
            tokens,
            names_filter=lambda name: "resid_post" in name,
        )

    next_token_logits = logits[0, -1]
    top_tokens = torch.topk(next_token_logits, k=top_k)

    top_next_tokens = []
    for value, token_id in zip(top_tokens.values, top_tokens.indices):
        top_next_tokens.append(
            {
                "token": model.to_string(token_id.item()),
                "token_id": int(token_id.item()),
                "logit": float(value.item()),
            }
        )

    resid_norms = []
    for layer in range(model.cfg.n_layers):
        resid = cache["resid_post", layer]
        final_token_resid = resid[0, -1]
        resid_norms.append(float(final_token_resid.norm().item()))

    return {
        "transformer_lens_token_shape": tuple(tokens.shape),
        "top_next_tokens": top_next_tokens,
        "resid_post_final_token_norms": resid_norms,
    }

def main():
    print("Torch:", torch.__version__)

    device, dtype = pick_device()
    print(f"Using device: {device}")
    print(f"Using dtype: {dtype}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    validate_all_prompts(tokenizer)

    model = HookedTransformer.from_pretrained_no_processing(
        MODEL_NAME,
        device=device,
        dtype=dtype,
    )

    for condition, row in prompts.items():
        for range_name, prompt in row.items():
            print(f"\nCondition: {condition}")
            print(f"Range: {range_name}")
            print(f"Prompt: {prompt!r}")

            result = run_prompt(model, prompt)

            print("TransformerLens token tensor shape:", result["transformer_lens_token_shape"])

            print("Top next-token guesses:")
            for item in result["top_next_tokens"]:
                print(f"  {item['token']!r} / id={item['token_id']} / logit={item['logit']:.3f}")

            print("Residual stream norm at final token by layer:")
            for layer, norm in enumerate(result["resid_post_final_token_norms"]):
                print(f"  layer {layer}: {norm:.6f}")

if __name__ == "__main__":
    main()