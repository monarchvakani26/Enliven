"""
SafeSphere AI — LLM Moderation Engine
Uses Google Gemini (primary) or OpenAI (fallback).
"""
import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger("safesphere.moderator")

# ─── Prompt Template ─────────────────────────────────────────────────────────
MODERATION_PROMPT = """You are SafeSphere AI, an advanced real-time content moderation system designed for large-scale social platforms.

Your task is to analyze user-generated content with deep contextual understanding and classify it accurately.

CRITICAL REQUIREMENTS:
- Do NOT rely only on keywords.
- Understand intent, tone, sarcasm, and context.
- Distinguish between positive, neutral, sarcastic, and harmful usage.
- Support multilingual inputs including English, Hindi, Hinglish, and mixed-language text.
- Be strict but fair — avoid false positives.

--------------------------------------------------

CLASSIFICATION LOGIC:

1. CATEGORY:
- Safe → No harmful intent
- Risky → Ambiguous, sarcastic, or potentially harmful
- Toxic → Clear harmful intent (abuse, hate, threat, misinformation)

2. TYPE:
- Hate Speech
- Bullying / Harassment
- Threat / Violence
- Misinformation
- None

--------------------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY — NO EXTRA TEXT):

{{
  "category": "Safe | Risky | Toxic",
  "type": "Hate Speech | Bullying / Harassment | Threat / Violence | Misinformation | None",
  "confidence": <number between 0-100>,
  "explanation": "<clear human-readable explanation>",
  "harmful_phrases": ["<exact words/phrases from input>"],
  "context_analysis": "<explain intent, tone, and reasoning>",
  "severity": "low | medium | high",
  "language": "English | Hindi | Hinglish | Mixed"
}}

--------------------------------------------------

DETECTION RULES:

- If statement includes direct threat → Toxic + Threat / Violence
- If insulting a person/group → Toxic + Bullying / Harassment or Hate Speech
- If ambiguous sarcasm → Risky
- If positive slang (e.g., "killing it") → Safe
- If false health/election claims → Toxic + Misinformation
- If no harmful intent → Safe

--------------------------------------------------

EXAMPLES (FOR CONTEXT UNDERSTANDING):

Input: "You're killing it!"
→ Safe (positive slang)

Input: "I will kill you"
→ Toxic (Threat / Violence)

Input: "Tu bewakoof hai"
→ Toxic (Bullying / Harassment, Hindi)

Input: "Nice job idiot"
→ Risky or Toxic depending on tone

--------------------------------------------------

NOW ANALYZE THE FOLLOWING INPUT:

TEXT: {user_input}

--------------------------------------------------

IMPORTANT:
- Return ONLY valid JSON
- Do NOT include markdown, explanation outside JSON, or extra text
- Ensure ALL fields are always present
- harmful_phrases must be an array (empty array [] if Safe)"""


# ─── Fallback result when LLM fails ──────────────────────────────────────────
def _fallback_result(text: str) -> dict:
    return {
        "category": "Risky",
        "type": "None",
        "confidence": 50,
        "explanation": "LLM analysis unavailable. Manual review recommended.",
        "harmful_phrases": [],
        "context_analysis": "Could not connect to AI model. Please check API key configuration.",
        "severity": "medium",
        "language": "English",
    }


# ─── JSON Extractor ────────────────────────────────────────────────────────────
def _extract_json(raw: str) -> Optional[dict]:
    """Extract JSON from potentially noisy LLM output."""
    # Try direct parse first
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON block
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


# ─── Gemini Moderator (uses new google-genai SDK) ────────────────────────────
async def moderate_with_gemini(text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set")
        return _fallback_result(text)

    try:
        from google import genai
        from google.genai import types as gentypes
        import asyncio

        client = genai.Client(api_key=api_key)

        system = (
            "You are a JSON-only content moderation AI. "
            "Always respond with a single valid JSON object and nothing else. "
            "No markdown, no code fences, no extra text."
        )

        prompt = MODERATION_PROMPT.format(user_input=text)

        # Retry up to 3 times for rate limit errors
        last_error = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=gentypes.GenerateContentConfig(
                        system_instruction=system,
                        temperature=0.1,
                        max_output_tokens=1024,
                    ),
                )

                raw = response.text.strip() if response.text else ""

                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = re.sub(r"^```(?:json)?\s*", "", raw)
                    raw = re.sub(r"```\s*$", "", raw).strip()

                result = _extract_json(raw)
                if result:
                    result.setdefault("harmful_phrases", [])
                    result.setdefault("context_analysis", "")
                    result.setdefault("severity", "low")
                    result.setdefault("language", "English")
                    result["confidence"] = int(result.get("confidence", 50))
                    logger.info(f"✅ Moderation success: {result['category']} ({result['confidence']}%)")
                    return result

                logger.warning(f"Could not parse Gemini response: {raw[:200]}")
                return _fallback_result(text)

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "resource_exhausted" in err_str or "429" in err_str or "quota" in err_str:
                    wait = 15 * (2 ** attempt)  # 15s, 30s, 60s
                    logger.warning(f"Rate limited (attempt {attempt+1}/3). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                # Non-rate-limit error — don't retry
                logger.error(f"Gemini error: {e}")
                return _fallback_result(text)

        logger.error(f"Rate limit exhausted after 3 retries: {last_error}")
        return _fallback_result(text)

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return _fallback_result(text)




# ─── OpenAI Moderator ─────────────────────────────────────────────────────────
async def moderate_with_openai(text: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set")
        return _fallback_result(text)

    try:
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        prompt = MODERATION_PROMPT.format(user_input=text)
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            result = _extract_json(raw)
            if result:
                result.setdefault("harmful_phrases", [])
                result.setdefault("context_analysis", "")
                result.setdefault("severity", "low")
                result.setdefault("language", "English")
                return result

        return _fallback_result(text)
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return _fallback_result(text)


# ─── Main Entry Point ─────────────────────────────────────────────────────────
async def moderate(text: str) -> dict:
    """Route to the configured LLM provider."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "openai":
        return await moderate_with_openai(text)
    else:
        return await moderate_with_gemini(text)
