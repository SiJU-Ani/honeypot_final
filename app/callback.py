
import logging
import requests
from app.config import GUVI_CALLBACK_URL

logger = logging.getLogger(__name__)


def _calculate_engagement_duration_seconds(messages):
    timestamps = [msg.get("timestamp") for msg in messages if isinstance(msg.get("timestamp"), (int, float))]
    if len(timestamps) < 2:
        return 0

    min_ts = min(timestamps)
    max_ts = max(timestamps)
    diff = max(0, max_ts - min_ts)

    # Heuristic: values above 1e12 are likely milliseconds
    if max_ts > 1_000_000_000_000:
        return int(diff / 1000)

    return int(diff)

def send_final_callback(session_id, session_data):
    suspicious_keywords = session_data.get("intelligence", {}).get("suspiciousKeywords", [])
    agent_notes = "Urgency-based scam detected"
    if suspicious_keywords:
        agent_notes = f"Detected suspicious intent via keywords: {', '.join(suspicious_keywords)}"

    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(session_data["messages"]),
        "engagementDurationSeconds": _calculate_engagement_duration_seconds(session_data["messages"]),
        "extractedIntelligence": session_data["intelligence"],
        "agentNotes": agent_notes
    }
    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
    except requests.RequestException:
        logger.exception("Failed to send final callback")
