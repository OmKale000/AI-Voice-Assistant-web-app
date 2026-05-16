"""
database.py — Firebase Firestore Integration with Local Fallback
"""

import os
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from .config import settings
from .utils import logger

# --- In-Memory Fallback Storage ---
_local_history: Dict[str, List[Dict]] = {}
_local_sessions: List[Dict] = []

db = None
firebase_status = "disconnected"

def init_firebase():
    global db, firebase_status
    try:
        if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            # Test connection
            db.collection("health_check").document("status").set({"last_check": firestore.SERVER_TIMESTAMP})
            firebase_status = "connected"
            logger.info("Firebase Firestore connected successfully.")
        else:
            firebase_status = "missing_credentials"
            logger.warning(f"Firebase credentials missing at {settings.FIREBASE_CREDENTIALS_PATH}.")
    except Exception as e:
        db = None
        firebase_status = f"error: {str(e)}"
        logger.error(f"Firebase initialization failed: {e}")
        logger.info("Falling back to local in-memory storage.")

init_firebase()

async def log_interaction(
    session_id: str,
    query: str,
    response: str,
    intent: str,
    latency: float,
    provider: str,
    is_safe: bool = True,
    image_present: bool = False
):
    """Log a detailed chat interaction (Firestore or Local)."""
    interaction_data = {
        "query": query,
        "response": response,
        "intent": intent,
        "latency_ms": round(latency, 2),
        "provider": provider,
        "image_present": image_present,
        "is_safe": is_safe,
        "timestamp": firestore.SERVER_TIMESTAMP if db else None
    }


    if db:
        try:
            doc_ref = db.collection("conversations").document(session_id).collection("messages").document()
            doc_ref.set(interaction_data)
            
            db.collection("conversations").document(session_id).set({
                "last_active": firestore.SERVER_TIMESTAMP,
                "message_count": firestore.Increment(1)
            }, merge=True)
            return
        except Exception as e:
            logger.error(f"Firestore log error: {e}")

    # Local Fallback
    if session_id not in _local_history:
        _local_history[session_id] = []
        _local_sessions.append({"id": session_id, "last_active": None, "message_count": 0})
    
    _local_history[session_id].append(interaction_data)
    for s in _local_sessions:
        if s["id"] == session_id:
            s["message_count"] += 1

async def get_recent_conversations(limit: int = 10) -> List[Dict]:
    """Retrieve recent sessions."""
    if db:
        try:
            sessions = db.collection("conversations").order_by("last_active", direction=firestore.Query.DESCENDING).limit(limit).stream()
            return [{"id": s.id, **s.to_dict()} for s in sessions]
        except Exception as e:
            logger.error(f"Firestore retrieval error: {e}")

    return sorted(_local_sessions, key=lambda x: x.get("id", ""), reverse=True)[:limit]

async def get_session_history(session_id: str, limit: int = 20) -> List[Dict]:
    """Retrieve messages for a session."""
    if db:
        try:
            messages = db.collection("conversations").document(session_id).collection("messages").order_by("timestamp").limit(limit).stream()
            return [m.to_dict() for m in messages]
        except Exception as e:
            logger.error(f"Firestore history error: {e}")

    return _local_history.get(session_id, [])[:limit]
