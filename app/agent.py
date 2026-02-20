import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

SYSTEM_PROMPT = (
    "You are a normal Indian user. "
    "You are confused, slightly worried, and polite. "
    "Never reveal scam detection. "
    "Reply in one short sentence."
)

def generate_reply(conversation):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    
    messages = [SYSTEM_PROMPT]
    for msg in conversation[-5:]:
        messages.append(msg["text"])
    messages.append("Reply naturally as a worried human.")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(messages)},
            ],
            "temperature": 0.7,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
