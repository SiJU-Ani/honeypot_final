
import re
from typing import List, Dict

def extract_intelligence(messages: List[Dict], store: dict):
    """Extract intelligence from scammer messages only"""
    
    # Use sets to prevent duplicates
    bank_accounts = set(store.get("bankAccounts", []))
    upi_ids = set(store.get("upiIds", []))
    phishing_links = set(store.get("phishingLinks", []))
    phone_numbers = set(store.get("phoneNumbers", []))
    suspicious_keywords = set(store.get("suspiciousKeywords", []))
    
    # Extract only from messages with sender="scammer"
    scammer_text = " ".join([msg["text"] for msg in messages if msg.get("sender", "").lower() == "scammer"])
    
    if not scammer_text:
        return
    
    # Extract UPI IDs (more precise pattern)
    upi_matches = re.findall(r"\b[\w][\w.-]{2,48}@[\w.-]+\b", scammer_text)
    # Filter out likely non-UPI emails
    for match in upi_matches:
        if any(domain in match.lower() for domain in ['@paytm', '@phonepe', '@ybl', '@okaxis', '@okicici', '@oksbi', '@okhdfcbank', '@freecharge', '@airtel', '@jio']):
            upi_ids.add(match)
        elif '@' in match and '.' not in match.split('@')[1]:  # UPI handles often don't have dots after @
            upi_ids.add(match)
    
    # Extract bank account numbers (12-18 digits, not phone numbers)
    accounts = re.findall(r"\b\d{12,18}\b", scammer_text)
    bank_accounts.update(accounts)
    
    # Extract phone numbers (Indian format with better patterns)
    # Matches: 9876543210, +919876543210, 91-9876543210, etc.
    phones = re.findall(r"(?:\+91[\s-]?|91[\s-]?|0)?([6-9]\d{9})\b", scammer_text)
    phone_numbers.update(phones)
    
    # Extract URLs (http/https and common link shorteners)
    links = re.findall(r"https?://[^\s]+", scammer_text)
    # Also catch common patterns without http
    suspicious_domains = re.findall(r"\b(?:bit\.ly|goo\.gl|tinyurl\.com|t\.co)/[\w-]+", scammer_text)
    phishing_links.update(links + suspicious_domains)
    
    # Extract suspicious keywords (expanded list)
    keywords = [
        "urgent", "verify", "blocked", "otp", "suspend", "freeze", "compromise", 
        "expire", "immediate", "cvv", "pin", "atm", "kyc", "security team",
        "customer care", "unauthorized", "fraudulent", "deactivate", "validate",
        "confirm", "authenticate", "prize", "won", "lottery", "refund", "cashback"
    ]
    for word in keywords:
        if word in scammer_text.lower():
            suspicious_keywords.add(word)
    
    # Update store with sorted, unique values
    store["bankAccounts"] = sorted(list(bank_accounts))
    store["upiIds"] = sorted(list(upi_ids))
    store["phishingLinks"] = sorted(list(phishing_links))
    store["phoneNumbers"] = sorted(list(phone_numbers))
    store["suspiciousKeywords"] = sorted(list(suspicious_keywords))
