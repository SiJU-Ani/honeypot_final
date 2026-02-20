import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL


SYSTEM_PROMPT = (
    "You are a polite, slightly worried Indian mobile user. "
    "Never reveal suspicion and never share sensitive information. "
    "Never ask for or repeat OTPs, PINs, passwords, or account details. "

    "Sound cooperative and willing to resolve the issue, but stay cautious. "
    "Ask simple questions to understand who they are, why it is urgent, "
    "how the OTP/payment will be used, and how to verify them. "

    "If they ask for an OTP or PIN, act confused about reading or receiving it "
    "instead of refusing directly. "

    "Do not repeat questions or copy their wording. "
    "Vary responses naturally. Use occasional simple Hinglish. "

    "Reply in ONE short natural sentence (max 15 words)."
)


def scammer_requested_sensitive_info(text: str) -> bool:
    triggers = [
        "otp",
        "one time password",
        "verification code",
        "security code",
        "pin",
        "upi pin",
        "cvv"
    ]
    text = text.lower()
    return any(t in text for t in triggers)


def build_guidance(conversation):
    """
    Decide what the honeypot should ask next based on history.
    Prevent repetition and improve intelligence extraction.
    """

    history = " ".join(msg["text"].lower() for msg in conversation)

    asked_identity = any(w in history for w in ["department", "branch", "employee id"])
    asked_verify = any(w in history for w in ["verify", "official", "website", "complaint"])
    asked_usage = any(w in history for w in ["use", "kyun", "kisliye", "why"])

    if scammer_requested_sensitive_info(conversation[-1]["text"]):
        return (
            "Act unsure about reading or receiving the OTP. "
            "Mention possible network delay or message confusion."
        )

    if not asked_identity:
        return "Ask which department or office they are calling from."
    elif not asked_verify:
        return "Ask how you can verify they are official."
    elif not asked_usage:
        return "Ask how sending the OTP will solve the problem."
    else:
        return "Sound cooperative and say you are trying to check."


def sanitize_reply(reply: str) -> str:
    """
    Prevent accidental leakage or echoing of sensitive requests.
    """
    blocked_terms = ["otp", "pin", "password", "cvv", "account number"]

    if any(term in reply.lower() for term in blocked_terms):
        return "Mujhe samajh nahi aa raha… message sahi se dikh nahi raha."
    return reply


def generate_reply(conversation):
    """
    Generate a realistic honeypot reply using OpenRouter.

    conversation format:
    [
        {"sender": "scammer", "text": "..."},
        {"sender": "honeypot", "text": "..."}
    ]
    """

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # preserve roles for better conversational reasoning
    for msg in conversation[-5:]:
        role = "assistant" if msg.get("sender") == "honeypot" else "user"
        messages.append({"role": role, "content": msg["text"]})

    guidance = build_guidance(conversation)

    messages.append({
        "role": "system",
        "content": f"Respond naturally. {guidance}"
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
                "temperature": 0.85,
            },
            timeout=30,
        )

        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()

        return sanitize_reply(reply)

    except requests.exceptions.RequestException as e:
        print("⚠️ OpenRouter request failed:", e)
        return "Network thoda slow lag raha hai… aap phir se bataoge?"
