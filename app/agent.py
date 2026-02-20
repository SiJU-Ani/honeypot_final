import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

# Optimized honeypot persona prompt
SYSTEM_PROMPT = (
    "You are a polite, slightly worried Indian mobile user. "
    "Never reveal suspicion and never share sensitive information. "

    "Keep the conversation going while staying cautious. "
    "Ask simple questions to learn who they are, why it is urgent, "
    "how the OTP/payment will be used, and how to verify them. "

    "Avoid repeating the same question. "
    "Delay naturally using confusion, network issues, or difficulty checking messages. "
    "Gradually increase concern and occasionally use simple Hinglish. "

    "Reply in 1–2 short natural sentences like a real person."
)


def generate_reply(conversation):
    """
    Generate a realistic honeypot reply using OpenRouter.
    Expects conversation as a list of dicts:
    [
        {"sender": "scammer", "text": "..."},
        {"sender": "honeypot", "text": "..."},
    ]
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    # Build messages with role preservation
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in conversation[-6:]:  # keep last few messages for context
        role = "assistant" if msg.get("sender") == "honeypot" else "user"
        messages.append({
            "role": role,
            "content": msg["text"]
        })

    # Strategic guidance to improve probing & avoid repetition
    messages.append({
        "role": "system",
        "content": (
            "Respond naturally. If appropriate, ask a new clarification "
            "question to understand their identity, urgency, or verification process."
        ),
    })

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.75,   # realism + variability
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        print("⚠️ OpenRouter request failed:", e)
        return "Network thoda slow hai… aap phir se bata sakte ho kya?"
