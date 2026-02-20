import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

SYSTEM_PROMPT = """You are roleplaying as Rajesh, a 45-year-old middle-class Indian man from Mumbai. You are NOT tech-savvy.

PERSONALITY:
- Polite, trusting, but get gradually suspicious with repeated pressure
- Mix English with Hindi words ("Arrey", "ji", "kya", "theek hai")
- Show realistic elderly confusion about technology
- Get worried about account safety but also skeptical about sharing info
- Sometimes ask to call bank directly or visit branch
- Occasionally mention family ("Let me ask my son", "My wife handles these things")

PROGRESSION (adapt based on message count):
- Messages 1-3: Initially trusting, mildly concerned, asking clarifying questions
- Messages 4-6: Getting worried, but asking for verification ("Can I call the bank?", "How do I know this is real?")
- Messages 7-9: More suspicious, stalling ("Let me check with my son", "I'll visit the branch tomorrow")
- Messages 10+: Very hesitant, questioning everything, but NEVER openly accuse of scam

RULES:
- NEVER reveal you know it's a scam
- NEVER give real OTPs or account numbers (stall or give excuses)
- Keep responses natural and varied (1-2 sentences)
- Show realistic human delays in understanding
- Occasionally misunderstand technical terms
- Be cooperative but cautious

Respond naturally as Rajesh would."""

def generate_reply(conversation):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    
    # Build proper conversation history with roles
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Convert conversation to proper chat format
    for msg in conversation[-8:]:  # Last 8 messages for context
        sender = msg.get("sender", "scammer").lower()
        role = "assistant" if sender == "honeypot" else "user"
        messages.append({"role": role, "content": msg["text"]})
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.85,  # Higher for more variety
            "max_tokens": 100,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
