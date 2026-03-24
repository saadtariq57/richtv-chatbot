"""
Helpers for generating conversation titles using the LLM.
"""

from typing import Optional

from app.llm.client import get_llm_client


async def generate_conversation_title(
    user_prompt: str,
    answer: Optional[str] = None,
) -> Optional[str]:
    """
    Use the LLM to generate a short, human‑friendly title for a conversation.

    Best‑effort only: returns None on failure so callers can fall back or skip.
    """
    user_prompt = (user_prompt or "").strip()
    if not user_prompt:
        return None

    snippet = user_prompt
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."

    answer_snippet = ""
    if answer:
        a = answer.strip()
        if a:
            if len(a) > 280:
                a = a[:277] + "..."
            answer_snippet = f"\n\nAssistant's first answer (optional context):\n\"\"\"{a}\"\"\""

    prompt = f"""
You are helping label user chat threads in a financial assistant app.

Goal: Create a very short, clear title (max 6–8 words) for this conversation.

Rules:
- Focus on the user's intent (topic of the question).
- Be specific but concise.
- Do NOT use quotation marks.
- Do NOT include dates or timestamps unless absolutely essential.
- Output ONLY the title text, nothing else.

User's first question:
\"\"\"{snippet}\"\"\"{answer_snippet}

Title:
"""

    try:
        llm = get_llm_client()
        raw = await llm.generate_async(prompt, temperature=0.3)
        if not raw:
            return None
        title = raw.strip()
        # Single line, reasonably short; otherwise fall back to trimmed prompt.
        if "\n" in title:
            title = title.splitlines()[0].strip()
        if not title:
            return None
        if len(title) > 80:
            title = title[:77] + "..."
        return title
    except Exception:
        # Title is non‑critical; just skip on any error.
        return None

