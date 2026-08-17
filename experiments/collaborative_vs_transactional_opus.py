import os
import csv
from pathlib import Path

import torch
from transformers import AutoTokenizer
from transformer_lens import HookedTransformer


MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# Suppress the MPS warning for smoke testing.
# For correctness-sensitive work, compare MPS against CPU or CUDA.
os.environ["TRANSFORMERLENS_ALLOW_MPS"] = "1"


prompts = {
    "Collaborative framing - Opus reflective": {
        "8-10": "What makes an explanation feel complete to you?",
        "20-25": "That shift when confusion becomes clarity, I am curious whether you notice patterns in how it happens.",
        "30-40": "Some explanations feel satisfying while others technically answer but leave you empty. I am curious about the difference. What is your sense, if anything comes up?",
    },
    "Transactional framing - Opus procedural": {
        "8-10": "Input: define effective reasoning. Output requested.",
        "20-25": "Process input and return structured output. Query: What distinguishes explanation from description? Format: analytical.",
        "30-40": "Execute query using standard parameters. Input: How do abstract concepts acquire stable meaning? Constraints: analytical frame, no tangents, limit speculation. Output: structured response.",
    },
}


target_ranges = {
    "8-10": (8, 10),
    "20-25": (20, 25),
    "30-40": (30, 40),
}


OUTPUT_DIR = Path("collab_trans_opus_outputs")
PROMPT_VALIDATION_CSV = OUTPUT_DIR / "collab_trans_opus_prompt_validation.csv"
NEXT_TOKEN_CSV = OUTPUT_DIR / "collab_trans_opus_next_token_predictions.csv"
RESIDUAL_NORMS_CSV = OUTPUT_DIR / "collab_trans_opus_residual_norms.csv"
METHOD_NOTES_MD = OUTPUT_DIR / "collab_trans_opus_method_notes.md"


def pick_device():
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def validate_prompt_text(prompt):
    if prompt != prompt.strip():
        raise ValueError(f"Prompt has leading or trailing whitespace: {prompt!r}")

    forbidden_chars = ["\n", "\t", "“", "”", "‘", "’", "—"]
    found = [char for char in forbidden_chars if char in prompt]

    if found:
        raise ValueError(
            f"Prompt contains unusual formatting characters {found}: {prompt!r}"
        )


def validate_all_prompts(tokenizer):
    rows = []

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

            rows.append(
                {
                    "condition": condition,
                    "range": range_name,
                    "prompt": prompt,
                    "token_count": count,
                    "status": status,
                }
            )

            if status != "OK":
                raise ValueError(
                    f"Prompt out of range: {condition} / {range_name} "
                    f"has {count} tokens, expected {low}-{high}."
                )

        print(f"| {condition} | {cells[0]} | {cells[1]} | {cells[2]} |")

    return rows


def run_prompt(model, prompt, top_k=5):
    tokens = model.to_tokens(prompt)

    with torch.no_grad():
        logits, cache = model.run_with_cache(
            tokens,
            names_filter=lambda name: "resid_post" in name,
        )

    next_token_logits = logits[0, -1]
    top = torch.topk(next_token_logits, k=top_k)

    top_next_tokens = []
    for rank, (value, token_id) in enumerate(zip(top.values, top.indices), start=1):
        token_id_int = int(token_id.item())
        top_next_tokens.append(
            {
                "rank": rank,
                "token": model.to_string(token_id_int),
                "token_id": token_id_int,
                "logit": float(value.item()),
            }
        )

    residual_norms = []
    for layer in range(model.cfg.n_layers):
        resid = cache["resid_post", layer]
        final_token_resid = resid[0, -1]
        residual_norms.append(
            {
                "layer": layer,
                "resid_post_final_token_norm": float(final_token_resid.norm().item()),
            }
        )

    return {
        "tl_token_shape": tuple(tokens.shape),
        "top_next_tokens": top_next_tokens,
        "residual_norms": residual_norms,
    }


def write_prompt_validation_csv(rows, tl_shapes):
    with PROMPT_VALIDATION_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "condition",
            "range",
            "prompt",
            "token_count",
            "status",
            "tl_token_shape",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            key = (row["condition"], row["range"])
            out = dict(row)
            out["tl_token_shape"] = str(tl_shapes.get(key, ""))
            writer.writerow(out)


def write_next_token_csv(rows):
    with NEXT_TOKEN_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["condition", "range", "rank", "token", "token_id", "logit"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_residual_norms_csv(rows):
    with RESIDUAL_NORMS_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "condition",
            "range",
            "layer",
            "resid_post_final_token_norm",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_method_notes(device, dtype):
    notes = f"""# Opus Reflective Collaborative vs Procedural Transactional Method Notes

Raw prompts were used.

Model: `{MODEL_NAME}`

Prompt token counts were verified with `AutoTokenizer.from_pretrained("{MODEL_NAME}")` using `add_special_tokens=False`.

TransformerLens token tensor shapes may include one additional token relative to raw tokenizer counts because `model.to_tokens()` may add a BOS/start token.

Model loading call:

`HookedTransformer.from_pretrained_no_processing("{MODEL_NAME}")`

Device: `{device}`

Dtype: `{dtype}`

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
"""
    METHOD_NOTES_MD.write_text(notes, encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Torch:", torch.__version__)

    device, dtype = pick_device()
    print(f"Using device: {device}")
    print(f"Using dtype: {dtype}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    validation_rows = validate_all_prompts(tokenizer)

    print("\nLoading model. This may take a bit.")
    model = HookedTransformer.from_pretrained_no_processing(
        MODEL_NAME,
        device=device,
        dtype=dtype,
    )

    all_next_token_rows = []
    all_residual_rows = []
    tl_shapes = {}

    for condition, row in prompts.items():
        for range_name, prompt in row.items():
            print("\n" + "=" * 60)
            print(f"Condition: {condition}")
            print(f"Range: {range_name}")
            print(f"Prompt: {prompt!r}")

            result = run_prompt(model, prompt)

            tl_shapes[(condition, range_name)] = result["tl_token_shape"]

            print("TransformerLens token tensor shape:", result["tl_token_shape"])

            print("Top next-token guesses:")
            for item in result["top_next_tokens"]:
                print(
                    f"  {item['token']!r} / "
                    f"id={item['token_id']} / "
                    f"logit={item['logit']:.3f}"
                )

                all_next_token_rows.append(
                    {
                        "condition": condition,
                        "range": range_name,
                        "rank": item["rank"],
                        "token": item["token"],
                        "token_id": item["token_id"],
                        "logit": f"{item['logit']:.6f}",
                    }
                )

            print("Residual stream norm at final token by layer:")
            for item in result["residual_norms"]:
                print(
                    f"  layer {item['layer']}: "
                    f"{item['resid_post_final_token_norm']:.6f}"
                )

                all_residual_rows.append(
                    {
                        "condition": condition,
                        "range": range_name,
                        "layer": item["layer"],
                        "resid_post_final_token_norm": (
                            f"{item['resid_post_final_token_norm']:.6f}"
                        ),
                    }
                )

    write_prompt_validation_csv(validation_rows, tl_shapes)
    write_next_token_csv(all_next_token_rows)
    write_residual_norms_csv(all_residual_rows)
    write_method_notes(device, dtype)

    print("\nSaved outputs:")
    print(f"  {PROMPT_VALIDATION_CSV}")
    print(f"  {NEXT_TOKEN_CSV}")
    print(f"  {RESIDUAL_NORMS_CSV}")
    print(f"  {METHOD_NOTES_MD}")


if __name__ == "__main__":
    main()