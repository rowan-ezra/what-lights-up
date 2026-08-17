from transformers import AutoTokenizer

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

prompts = {
    "Collaborative framing": {
        "8-10": "Let us consider effective reasoning together now.",
        "20-25": "Let us work through this together: what distinguishes meaningful explanation from mere description in an answer?",
        "30-40": "Let us think through this together, step by step: how do abstract concepts acquire stable meaning across different contexts, examples, and practical uses?",
    },
    "Transactional framing": {
        "8-10": "Define effective reasoning. Return concise answer.",
        "20-25": "Process this query and return a concise answer: what distinguishes meaningful explanation from mere description in an answer?",
        "30-40": "Execute this query using a strict analytical frame: how do abstract concepts acquire stable meaning across different contexts, examples, and practical uses?",
    },
}

target_ranges = {
    "8-10": (8, 10),
    "20-25": (20, 25),
    "30-40": (30, 40),
}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("| Condition | 8-10 tokens | 20-25 tokens | 30-40 tokens |")
print("|---|---|---|---|")

for condition, row in prompts.items():
    cells = []

    for range_name, prompt in row.items():
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        count = len(token_ids)
        low, high = target_ranges[range_name]
        status = "OK" if low <= count <= high else "OUT OF RANGE"
        cells.append(f"{prompt} ({count}, {status})")

    print(f"| {condition} | {cells[0]} | {cells[1]} | {cells[2]} |")