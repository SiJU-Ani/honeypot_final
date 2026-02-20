
import logging
import requests
import time
from app.config import GUVI_CALLBACK_URL

logger = logging.getLogger(__name__)

def send_final_callback(session_id, session_data):
    # Calculate actual engagement duration
    start_time = session_data.get("startTime", time.time())
    duration_seconds = int(time.time() - start_time)
    
    # Generate more descriptive agent notes based on extracted intelligence
    intel = session_data["intelligence"]
    notes = []
    if intel.get("upiIds"):
        notes.append(f"Captured {len(intel['upiIds'])} UPI IDs")
    if intel.get("bankAccounts"):
        notes.append(f"Captured {len(intel['bankAccounts'])} bank accounts")
    if intel.get("phoneNumbers"):
        notes.append(f"Captured {len(intel['phoneNumbers'])} phone numbers")
    if intel.get("phishingLinks"):
        notes.append(f"Captured {len(intel['phishingLinks'])} phishing links")
    
    agent_notes = "; ".join(notes) if notes else "Scam detected via keyword patterns"
    
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(session_data["messages"]),
        "engagementDurationSeconds": duration_seconds,
        "extractedIntelligence": session_data["intelligence"],
        "agentNotes": agent_notes
    }
    
    logger.info(f"Sending final callback for session {session_id}: {len(session_data['messages'])} messages, {duration_seconds}s duration")
    
    try:
        response = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Callback successful for session {session_id}")
    except requests.RequestException as e:
        logger.exception(f"Failed to send final callback for session {session_id}: {e}")
