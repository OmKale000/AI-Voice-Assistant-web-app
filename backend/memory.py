"""
memory.py — Conversation Memory Window Management.
"""

from typing import List, Dict
from .config import settings

def get_truncated_history(history: List[Dict[str, str]], max_turns: int = None) -> List[Dict[str, str]]:
    """
    Returns a truncated version of the chat history to prevent token explosion.
    Maintains the rolling window specified in settings.
    """
    limit = max_turns or settings.MAX_HISTORY_MESSAGES
    # Each exchange is 2 messages (user + assistant)
    # So max_messages = limit * 2
    max_messages = limit * 2
    
    if len(history) <= max_messages:
        return history
        
    return history[-max_messages:]
