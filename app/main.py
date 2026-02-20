import logging


from fastapi import FastAPI, Header, HTTPException
from app.schemas import RequestSchema
from app.config import API_KEY, OPENROUTER_API_KEY
from app.scam_detector import detect_scam
from app.agent import generate_reply
from app.intelligence import extract_intelligence
from app.memory import get_session
from app.callback import send_final_callback

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s"
)


@app.on_event("startup")
def validate_openrouter_config():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")


@app.post("/honeypot")
def honeypot(data: RequestSchema, x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session = get_session(data.sessionId)
    session["messages"].append(data.message.dict())

    if detect_scam(data.message.text):
        session["scamDetected"] = True
        extract_intelligence(session["messages"], session["intelligence"])

    try:
        reply = generate_reply(session["messages"])

    except Exception as e:
        logger.exception("LLM failed, using fallback")
        reply = "I am not understanding this properly. Can you explain again?"

    # Send callback after sufficient engagement (10+ messages) and only once
    if session["scamDetected"] and len(session["messages"]) >= 10:
        if not session.get("callbackSent", False):
            send_final_callback(data.sessionId, session)
            session["callbackSent"] = True
            logger.info(f"Session {data.sessionId}: Scam detected, callback sent after {len(session['messages'])} messages")

    return {"status": "success", "reply": reply}
