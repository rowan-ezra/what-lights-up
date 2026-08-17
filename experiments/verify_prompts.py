from transformers import AutoTokenizer

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

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