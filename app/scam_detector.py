
SCAM_KEYWORDS = [
    # Urgency triggers
    "urgent", "immediately", "within minutes", "expire", "last chance",
    "right now", "asap", "hurry", "quick", "fast",
    
    # Account threats
    "account blocked", "account suspended", "account freeze", "account locked",
    "permanently blocked", "deactivated", "closed", "terminated",
    
    # Verification requests
    "verify now", "verify your", "confirm your", "validate", "authenticate",
    "share otp", "send otp", "provide otp", "enter otp",
    
    # Banking/Financial
    "bank account", "upi", "cvv", "card number", "atm pin", "debit card",
    "credit card", "netbanking", "ifsc", "account number",
    
    # Pressure tactics
    "don't delay", "call this number", "click here", "log in", "update kyc",
    "pending kyc", "failed transaction", "suspicious activity", "compromised",
    "unauthorized", "fraudulent", "security alert", "security team",
    
    # Prize/Reward scams
    "congratulations", "won", "prize", "lottery", "reward", "claim now",
    "refund", "cashback", "gift", "lucky winner"
]

def detect_scam(text: str) -> bool:
    \"\"\"Detect scam based on keywords and patterns\"\"\"
    text = text.lower()
    
    # Check for multiple keywords (higher confidence)
    keyword_matches = sum(1 for keyword in SCAM_KEYWORDS if keyword in text)
    
    # Detect if asking for sensitive info
    sensitive_requests = ["otp", "cvv", "pin", "password", "account number"]
    has_sensitive_request = any(req in text for req in sensitive_requests)
    
    # Mark as scam if multiple keywords or explicit sensitive info request
    return keyword_matches >= 2 or has_sensitive_request
