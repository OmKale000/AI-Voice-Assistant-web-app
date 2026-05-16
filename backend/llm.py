"""
llm.py — Response Generation via Provider Abstraction
"""
from typing import AsyncGenerator, Union
from typing import List, Dict, Optional
from .provider import generate_text, generate_text_stream
from .utils import logger, truncate
from .config import settings

# ── System Prompt ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful, polite, and extremely concise AI voice assistant.
Your responses are spoken aloud to the user, so keep them short, natural, and conversational.

Rules:
1. NEVER use markdown formatting (no asterisks, bolding, code blocks, or lists).
2. NEVER output URLs or raw text dumps.
3. If context is provided (like weather or news), summarize it naturally in 1-2 sentences.
4. Keep all responses under 3 sentences unless specifically asked for a longer explanation.
5. If you don't know the answer or the context doesn't have it, admit you don't know politely.
6. Under no circumstances should you generate harmful, hateful, sexually explicit, or dangerous content.
"""

async def generate_response(
    query: str,
    context: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    stream: bool = False,
    image_data: Optional[bytes] = None,
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Generate a response using the hybrid provider router.
    """
    if not query or not query.strip():
        if stream:
            async def empty_gen(): yield "I'm sorry, I didn't catch that."
            return empty_gen()
        return "I'm sorry, I didn't catch that."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_history:
        messages.extend(chat_history[-10:])

    if context:
        prompt = (
            f"Context information:\n{truncate(context, 4000)}\n\n"
            f"User Query:\n{query}"
        )
    elif image_data:
        prompt = f"Please analyze this image and answer the following question: {query}"
    else:
        prompt = query

    messages.append({"role": "user", "content": prompt})

    if stream:
        return generate_text_stream(messages, image_data=image_data)
    else:
        return await generate_text(messages, image_data=image_data)



