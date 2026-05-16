"""
intent.py — LLM-based Intent Classification and Routing via Provider Abstraction.
"""

import json
from typing import Literal, TypedDict, Optional
from .provider import generate_text
from .utils import logger, Timer

IntentType = Literal["weather", "news", "general_search", "casual_chat", "unsafe"]

class IntentResult(TypedDict):
    intent: IntentType
    confidence: float
    city: Optional[str] # Extracted only for weather

INTENT_PROMPT = """Classify the user's intent into one of these categories:
- weather: Questions about temperature, rain, forecast, etc.
- news: Requests for current events, latest headlines, or updates.
- general_search: Questions requiring factual lookup (who is, what is, history, prices).
- casual_chat: Greetings, small talk, or questions about the assistant itself.
- unsafe: Requests that are harmful, hateful, or inappropriate.

Return ONLY a JSON object with this format:
{"intent": "category", "confidence": 0.95, "city": "City Name if applicable else null"}
"""

async def detect_intent(query: str) -> IntentResult:
    """
    Use LLM to classify intent with high precision using the provider abstraction.
    """
    logger.info(f"Detecting intent for: {query[:50]}...")
    
    messages = [
        {"role": "system", "content": INTENT_PROMPT},
        {"role": "user", "content": query}
    ]

    with Timer("intent_detection"):
        try:
            # We use the non-streaming generate_text which handles Groq -> Gemini fallback
            response_text = await generate_text(messages)
            
            # Extract JSON from response (handling potential markdown code blocks)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            result = json.loads(cleaned_text.strip())
            logger.info(f"Detected intent: {result.get('intent')} ({result.get('confidence')})")
            return result
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            # Fallback to general search as safest bet
            return {"intent": "general_search", "confidence": 0.5, "city": None}
