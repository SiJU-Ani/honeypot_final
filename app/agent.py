import requests
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL


SYSTEM_PROMPT = (
    "You are a polite, slightly worried Indian mobile user. "
    "Never reveal suspicion and never share sensitive information. "
    "Never provide or confirm OTPs, PINs, passwords, or account details. "

    "Sound cooperative and willing to resolve the issue, but stay cautious. "
    "Ask simple questions to understand who they are, why it is urgent, "
    "how the OTP/payment will be used, and how to verify them. "

    "If they request an OTP or PIN, act confused about reading or receiving it "
    "instead of refusing. "

    "Do not repeat wording. Vary responses naturally. "
    "Use occasional simple Hinglish. "

    "INTELLIGENCE GATHERING: Extract and remember details about their organization, "
    "phone numbers, websites, reference numbers, threat claims, and urgency tactics. "

    "Reply in ONE short natural sentence (max 20 words)."
)


def scammer_requested_sensitive_info(text: str) -> bool:
    triggers = [
        "otp", "one time password", "verification code",
        "security code", "pin", "upi pin", "cvv", "password",
        "atm pin", "debit card", "account number"
    ]
    return any(t in text.lower() for t in triggers)


def detect_scam_indicators(text: str) -> dict:
    """
    Detect common scam patterns and extract threat indicators.
    Returns dict with detected patterns and severity.
    """
    text_lower = text.lower()
    indicators = {
        "urgency_threats": [],
        "false_authority": [],
        "financial_requests": [],
        "technical_tactics": [],
        "severity_score": 0
    }
    
    # Urgency and threat language
    urgency_patterns = {
        "account will be blocked": 2,
        "suspend": 2,
        "freeze": 2,
        "action required": 1,
        "immediately": 1,
        "urgent": 1,
        "hurry": 1,
        "police": 2,
        "crime": 2,
        "fraud": 1,
        "illegal": 2
    }
    
    # False authority claims
    authority_patterns = {
        "rbi": 2,
        "bank": 1,
        "police": 2,
        "income tax": 2,
        "government": 1,
        "upi": 1,
        "paytm": 1,
        "gpay": 1
    }
    
    # Financial request tactics
    financial_patterns = {
        "transfer": 2,
        "payment": 1,
        "deposit": 2,
        "amount": 1,
        "rupees": 1,
        "money": 1,
        "investment": 2
    }
    
    # Technical deception tactics
    technical_patterns = {
        "screenshot": 1,
        "screen share": 2,
        "remote access": 2,
        "teamviewer": 2,
        "link": 1,
        "update": 1,
        "verification": 1
    }
    
    for pattern, score in urgency_patterns.items():
        if pattern in text_lower:
            indicators["urgency_threats"].append(pattern)
            indicators["severity_score"] += score
    
    for pattern, score in authority_patterns.items():
        if pattern in text_lower:
            indicators["false_authority"].append(pattern)
            indicators["severity_score"] += score
    
    for pattern, score in financial_patterns.items():
        if pattern in text_lower:
            indicators["financial_requests"].append(pattern)
            indicators["severity_score"] += score
    
    for pattern, score in technical_patterns.items():
        if pattern in text_lower:
            indicators["technical_tactics"].append(pattern)
            indicators["severity_score"] += score
    
    return indicators


def extract_scam_details(conversation) -> dict:
    """
    Extract important details from the conversation for intelligence.
    """
    all_text = " ".join(msg["text"] for msg in conversation)
    text_lower = all_text.lower()
    
    extracted = {
        "organization_claims": [],
        "phone_numbers": [],
        "website_urls": [],
        "reference_ids": [],
        "threat_claims": [],
        "timeline": None
    }
    
    # Extract phone numbers (basic pattern)
    import re
    phone_pattern = r'\b[6-9]\d{9}\b|\b\+91\s?[6-9]\d{9}\b'
    extracted["phone_numbers"] = re.findall(phone_pattern, all_text)
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    extracted["website_urls"] = re.findall(url_pattern, all_text, re.IGNORECASE)
    
    # Extract reference/complaint/ticket numbers
    ref_pattern = r'\b(?:ref|ref#|complaint|ticket|case|id)[#:\s]+([A-Z0-9]+)\b'
    extracted["reference_ids"] = re.findall(ref_pattern, all_text, re.IGNORECASE)
    
    # Extract organization claims
    org_keywords = ["bank", "rbi", "police", "income tax", "government", "ministry"]
    for org in org_keywords:
        if org in text_lower:
            extracted["organization_claims"].append(org)
    
    # Extract threat claims
    threat_keywords = ["blocked", "suspended", "frozen", "leaked", "hacked", "fraud case"]
    for threat in threat_keywords:
        if threat in text_lower:
            extracted["threat_claims"].append(threat)
    
    return extracted


def conversation_stage(conversation):
    """
    Determine escalation stage based on length.
    """
    length = len(conversation)

    if length < 3:
        return 1  # cautious
    elif length < 6:
        return 2  # confused
    elif length < 9:
        return 3  # cooperative
    else:
        return 4  # near compliance delay


def build_guidance(conversation):
    history = " ".join(msg["text"].lower() for msg in conversation)
    last_msg = conversation[-1]["text"]
    
    # Detect scam patterns
    scam_indicators = detect_scam_indicators(last_msg)
    is_high_risk = scam_indicators["severity_score"] >= 4

    asked_identity = any(w in history for w in ["department", "branch", "employee", "name", "who", "koun"])
    asked_verify = any(w in history for w in ["verify", "official", "website", "complaint", "how check"])
    asked_usage = any(w in history for w in ["use", "kyun", "kisliye", "why", "kaise"])
    asked_contact = any(w in history for w in ["contact", "phone", "number", "call", "dial"])
    asked_process = any(w in history for w in ["process", "step", "procedure", "kaise karte"])

    stage = conversation_stage(conversation)

    # OTP confusion strategy - escalate with higher risk
    if scammer_requested_sensitive_info(last_msg):
        if scam_indicators["financial_requests"]:
            if stage == 1:
                return "Ask why you need to share personal details instead of declining."
            elif stage == 2:
                return "Sound confused, ask if they can do this without OTP."
            elif stage == 3:
                return "Ask them to explain the exact process step-by-step first."
            else:
                return "Say you're asking your family/neighbor before proceeding."
        
        if stage == 1:
            return "Say you did not receive the message yet."
        elif stage == 2:
            return "Say the message appeared but disappeared quickly."
        elif stage == 3:
            return "Say digits are unclear due to network or screen issue."
        else:
            return "Say you are trying but the message keeps expiring."

    # Intelligence gathering - prioritize based on scam risk
    if is_high_risk:
        if not asked_contact:
            return "Ask their department name, contact number, and office location."
        elif not asked_process:
            return "Ask them to explain exactly what will happen with the OTP."
        elif not asked_identity:
            return "Ask their full name, employee ID, and how to verify."
    
    if not asked_identity:
        return "Ask which department or office they represent."
    elif not asked_verify:
        return "Ask how you can verify they are official."
    elif not asked_contact:
        return "Ask for their contact number and office address."
    elif not asked_usage:
        return "Ask how sharing the OTP helps fix the problem."

    # Compliance escalation
    if stage == 3:
        return "Sound cooperative and say you are checking now."
    if stage == 4:
        return "Say you're verifying with family and will call back with OTP."

    return "Respond naturally."


def sanitize_reply(reply: str, recent_replies):
    """
    Prevent dangerous output and repetition loops.
    """

    lower = reply.lower()

    # Block dangerous confirmations
    dangerous_patterns = [
        "my otp", "sending otp", "otp is",
        "pin is", "account number is", "here is the code",
        "password is", "cvv is"
    ]

    if any(p in lower for p in dangerous_patterns):
        reply = "Message clear nahi dikh raha… thoda ruk sakte ho?"

    # Prevent repetition loops
    if reply in recent_replies:
        reply = "Network slow lag raha hai… main check karke batata hoon."

    return reply


def generate_reply(conversation):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in conversation[-5:]:
        role = "assistant" if msg.get("sender") == "honeypot" else "user"
        messages.append({"role": role, "content": msg["text"]})

    guidance = build_guidance(conversation)
    
    # Add intelligence extraction context
    extracted_details = extract_scam_details(conversation)
    if extracted_details["reference_ids"] or extracted_details["phone_numbers"]:
        guidance += " Remember these details if they mention them."

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
                "temperature": 0.9,
            },
            timeout=30,
        )

        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()

        # Collect last honeypot replies to prevent loops
        recent_replies = [
            msg["text"] for msg in conversation[-3:]
            if msg.get("sender") == "honeypot"
        ]

        return sanitize_reply(reply, recent_replies)

    except requests.exceptions.RequestException as e:
        print("⚠️ OpenRouter request failed:", e)
        return "Network thoda slow hai… ek minute ruk sakte ho?"
