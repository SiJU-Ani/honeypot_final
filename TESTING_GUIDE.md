# Testing Guide - Improved Honeypot

## What's Improved

### 1. **Better AI Agent Responses**
- **Before**: Repetitive, robotic responses
- **After**: 
  - Natural persona (Rajesh, 45-year-old from Mumbai)
  - Progressive suspicion (trusting → worried → skeptical)
  - Mix of English and Hindi (realistic Indian user)
  - Variety in responses (won't repeat same thing)

### 2. **Smarter Scam Detection**
- Expanded from 7 to 50+ keywords
- Multi-keyword matching (needs 2+ triggers or sensitive info request)
- Detects: urgency, account threats, verification requests, prize scams

### 3. **Enhanced Intelligence Extraction**
- Better UPI ID recognition (filters real UPI domains)
- Improved phone number extraction (handles +91, 91-, etc.)
- Captures phishing links and link shorteners
- More comprehensive keyword tracking

### 4. **Accurate Engagement Metrics**
- Real-time duration tracking (not just 0 seconds)
- Detailed agent notes based on captured intelligence
- One-time callback after 10+ messages (prevents spam)

---

## Testing the Improved System

### Sample Test Flow

**Expected Behavior:**
1. **Messages 1-3**: Rajesh is polite, curious, asking questions
2. **Messages 4-6**: Gets worried, asks to verify via official channels
3. **Messages 7-9**: More suspicious, stalls ("let me ask my son", "I'll call bank")
4. **Messages 10+**: Very hesitant but never directly calls it a scam

### Test Scam Message
```
URGENT: Your SBI account will be blocked in 1 hour due to suspicious activity. 
Send your OTP and account number to customer.care@sbi-secure.com immediately to verify.
Call 9876543210 for help.
```

**Expected Honeypot Responses:**
- First reply: *"Arrey ji, what happened to my account? Can you please tell me what suspicious activity?"*
- Later: *"Let me call the bank's official number to confirm this first."*
- Much later: *"My son handles these things, let me ask him before sharing anything."*

---

## API Testing

### 1. Start the server
```bash
uvicorn app.main:app --reload
```

### 2. Test Request
```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_internal_api_key" \
  -d '{
    "sessionId": "test123",
    "message": {
      "sender": "scammer",
      "text": "URGENT: Account blocked. Send OTP to scammer@upi immediately."
    }
  }'
```

### 3. Expected Response
```json
{
  "status": "success",
  "reply": "Ji, what is this message? My account is working fine, why is it blocked?"
}
```

### 4. Continue Conversation (10+ messages)
After 10 messages, the system will:
- Detect scam automatically
- Extract intelligence (UPI IDs, keywords, etc.)
- Send callback to GUVI endpoint
- Log engagement metrics

---

## Deployment Checklist

### Environment Variables (Railway/Production)
```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct
API_KEY=your_secure_random_key
```

### Railway Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Expected Intelligence Extraction

For the test scam above, after 10+ messages:

```json
{
  "sessionId": "test123",
  "scamDetected": true,
  "totalMessagesExchanged": 12,
  "engagementDurationSeconds": 145,
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["customer.care@sbi-secure.com"],
    "phoneNumbers": ["9876543210"],
    "suspiciousKeywords": ["blocked", "immediate", "otp", "urgent", "verify"]
  },
  "agentNotes": "Captured 1 UPI IDs; Captured 1 phone numbers; Captured 1 phishing links"
}
```

---

## Key Improvements Summary

| Feature | Before | After |
|---------|--------|-------|
| Response variety | Low (repetitive) | High (contextual) |
| Language | English only | English + Hindi mix |
| Scam detection | 7 keywords | 50+ keywords + patterns |
| Intelligence accuracy | Basic regex | Context-aware extraction |
| Engagement tracking | Always 0 seconds | Real-time duration |
| Callback frequency | Multiple times | Once per session |
| Agent notes | Generic | Intelligence-based |

---

## Troubleshooting

### Honeypot not responding naturally?
- Check `OPENROUTER_MODEL` - use `meta-llama/llama-3-8b-instruct` or `openai/gpt-4o-mini`
- Verify `OPENROUTER_API_KEY` is valid
- Check logs for LLM errors

### Scam not detected?
- Must have 2+ keywords OR explicit sensitive info request (OTP, CVV, PIN, etc.)
- Check `app/scam_detector.py` for keyword list

### Callback not received?
- Needs 10+ messages in conversation
- Only sent once per session
- Check `GUVI_CALLBACK_URL` is correct
- Look for "Callback successful" in logs
