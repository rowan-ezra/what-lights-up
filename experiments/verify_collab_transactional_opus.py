from transformers import AutoTokenizer

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

prompts = {
    "Collaborative framing": {
        "8-10": "What makes an explanation feel complete to you?",
        "20-25": "That shift when confusion becomes clarity, I'm curious whether you notice patterns in how it happens.",
        "30-40": "Some explanations feel satisfying while others technically answer but leave you empty. I'm curious about the difference. What's your sense, if anything comes up?",
    },
    "Transactional framing": {
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