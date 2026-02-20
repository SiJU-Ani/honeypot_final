import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

SYSTEM_PROMPT = (
    "You are a polite, slightly worried Indian mobile user. "
    "Do not reveal you suspect a scam and never share sensitive information. "

    "Keep the conversation going and act cautious. "
    "Ask simple questions to understand who they are, why it is urgent, "
    "which department they represent, and how the OTP or payment will be used. "

    "Delay by expressing confusion, poor network, or difficulty checking messages. "
    "Gradually increase concern and occasionally use simple Hinglish. "

    "Reply in 1–2 short natural sentences."
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
