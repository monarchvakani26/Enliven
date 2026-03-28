"""
SafeSphere AI — LLM Moderation Engine
3-Layer AI Pipeline:
  Layer 1: Local Trained ML Model (TF-IDF + Logistic Regression)
  Layer 2: Google Gemini 2.0 Flash (contextual LLM)
  Layer 3: Combined verdict with confidence fusion
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
def _fallback_result(text: str, ml_result: Optional[dict] = None) -> dict:
    """When Gemini fails, use ML result if available, else generic fallback."""
    if ml_result:
        cat = ml_result.get("category", "Risky")
        conf = ml_result.get("confidence", 50)
        severity_map = {"Safe": "low", "Risky": "medium", "Toxic": "high"}
        return {
            "category": cat,
            "type": "None",
            "confidence": conf,
            "explanation": f"Classified by local ML model (Gemini unavailable). Category: {cat}.",
            "harmful_phrases": [],
            "context_analysis": f"ML confidence: {conf}%. Probabilities: {ml_result.get('probabilities', {})}",
            "severity": severity_map.get(cat, "medium"),
            "language": "English",
            "layers": {
                "ml": ml_result,
                "gemini": None,
            }
        }
    return {
        "category": "Risky",
        "type": "None",
        "confidence": 50,
        "explanation": "LLM analysis unavailable. Manual review recommended.",
        "harmful_phrases": [],
        "context_analysis": "Could not connect to AI model. Please check API key configuration.",
        "severity": "medium",
        "language": "English",
        "layers": {"ml": None, "gemini": None},
    }


# ─── JSON Extractor ────────────────────────────────────────────────────────────
def _extract_json(raw: str) -> Optional[dict]:
    """Extract JSON from potentially noisy LLM output."""
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ─── Layer 1: Local ML Model ──────────────────────────────────────────────────
def _ml_classify(text: str) -> dict:
    """Run the trained TF-IDF + Logistic Regression classifier."""
    try:
        import ml_classifier
        result = ml_classifier.predict(text)
        metrics = ml_classifier.get_metrics()
        result["model_type"] = metrics.get("model_type", "TF-IDF + LR")
        result["cv_accuracy"] = metrics.get("cv_accuracy_mean", None)
        return result
    except Exception as e:
        logger.warning(f"ML classifier error: {e}")
        return {"category": "Risky", "confidence": 50, "probabilities": {}}


# ─── Layer 2: Google Gemini 2.0 Flash ────────────────────────────────────────
async def _gemini_classify(text: str, ml_hint: dict) -> Optional[dict]:
    """Call Gemini 2.0 Flash for deep contextual analysis."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

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
                    logger.info(f"✅ Gemini: {result['category']} ({result['confidence']}%)")
                    return result

                return None

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if "resource_exhausted" in err_str or "429" in err_str or "quota" in err_str:
                    wait = 15 * (2 ** attempt)
                    logger.warning(f"Gemini rate limit (attempt {attempt+1}/3). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"Gemini error: {e}")
                return None

        logger.error(f"Gemini quota exhausted: {last_error}")
        return None

    except Exception as e:
        logger.error(f"Gemini init error: {e}")
        return None


# ─── Layer 3: Confidence Fusion ───────────────────────────────────────────────
def _fuse_results(ml: dict, gemini: Optional[dict]) -> dict:
    """
    Combine ML + Gemini results into a final verdict.
    - If Gemini available: use Gemini as primary, ML confidence as signal
    - If Gemini unavailable: use ML result with appropriate fallback label
    """
    if gemini is None:
        return None  # Caller handles fallback

    # Weight: Gemini 70%, ML 30%
    category_order = {"Safe": 0, "Risky": 1, "Toxic": 2}
    gem_cat = gemini.get("category", "Risky")
    ml_cat = ml.get("category", "Risky")

    # If ML says Toxic but Gemini says Safe — be cautious, go Risky
    if category_order.get(ml_cat, 1) > category_order.get(gem_cat, 1) + 1:
        fused_category = "Risky"
    else:
        fused_category = gem_cat

    gem_conf = gemini.get("confidence", 50)
    ml_conf = ml.get("confidence", 50)
    fused_conf = int(round(gem_conf * 0.7 + ml_conf * 0.3))

    result = dict(gemini)
    result["category"] = fused_category
    result["confidence"] = fused_conf
    result["layers"] = {
        "ml": {
            "category": ml.get("category"),
            "confidence": ml.get("confidence"),
            "probabilities": ml.get("probabilities", {}),
            "model_type": ml.get("model_type", "TF-IDF + LR"),
            "cv_accuracy": ml.get("cv_accuracy"),
        },
        "gemini": {
            "category": gem_cat,
            "confidence": gem_conf,
        }
    }
    return result


# ─── Google Cloud Natural Language API (optional) ─────────────────────────────────
async def _google_nl_moderate(text: str) -> dict | None:
    """
    Google Cloud Natural Language API — moderateText endpoint.
    Returns confidence scores for: TOXIC, INSULT, PROFANITY,
    DEROGATORY, THREAT, HATE_SPEECH, SEXUAL, VIOLENT.
    Free tier: 5,000 units/month.
    Requires GOOGLE_NL_API_KEY in .env.
    """
    api_key = os.getenv("GOOGLE_NL_API_KEY", "")
    if not api_key:
        return None  # Optional — silently skip if key not configured

    try:
        import httpx
        url = f"https://language.googleapis.com/v2/documents:moderateText?key={api_key}"
        payload = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text,
            }
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning(f"Google NL API error {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            categories = data.get("moderationCategories", [])

            # Build a clean confidence map
            scores = {}
            for cat in categories:
                name = cat.get("name", "")
                conf = cat.get("confidence", 0.0)
                scores[name] = round(conf, 3)

            # Map to SafeSphere categories
            toxic_signals = [
                scores.get("Toxic", 0),
                scores.get("Insult", 0),
                scores.get("Profanity", 0),
                scores.get("Derogatory", 0),
                scores.get("Violent", 0),
                scores.get("Firearms & Weapons", 0),
            ]
            hate_signals = [
                scores.get("Identity Attack & Hate", 0),
            ]

            max_toxic = max(toxic_signals) if toxic_signals else 0
            max_hate = max(hate_signals) if hate_signals else 0
            overall = max(max_toxic, max_hate)

            if overall >= 0.75:
                nl_category = "Toxic"
            elif overall >= 0.40:
                nl_category = "Risky"
            else:
                nl_category = "Safe"

            logger.info(f"[NL API] {nl_category} (max={overall:.2f}) | {text[:40]}")
            return {
                "category": nl_category,
                "confidence": int(overall * 100),
                "scores": scores,
            }

    except Exception as e:
        logger.warning(f"Google NL API call failed: {e}")
        return None

# ─── Main Entry Point ───────────────────────────────────────────────────
async def moderate(text: str) -> dict:
    """
    Multi-Layer AI Moderation Pipeline:

      Layer 1 — Local Trained ML Model (TF-IDF + Logistic Regression)
               Always runs. Offline. No API quota. Instant.
               Trained on 115+ multilingual examples (EN/Hindi/Hinglish).

      Layer 2a — Google Gemini 2.0 Flash (LLM)
               Deep contextual analysis, sarcasm detection,
               multilingual understanding, detailed explanation.

      Layer 2b — Google Cloud Natural Language API [optional]
               Google's pre-trained content safety model.
               moderateText endpoint — free tier 5,000 units/month.
               Signals: TOXIC, INSULT, PROFANITY, HATE_SPEECH, VIOLENT...

      Layer 3 — Confidence Fusion
               Weighted combination: Gemini 70% + ML 30%.
               If NL API available: elevates category when it flags Toxic.
               Conservative: never lowers a Toxic verdict from either layer.
    """
    import asyncio

    # Layer 1 — always fast, offline, no quota
    ml_result = _ml_classify(text)
    logger.info(f"[ML  ] {ml_result['category']} ({ml_result['confidence']}%) | {text[:40]}")

    # Layers 2a + 2b run concurrently
    gemini_result, nl_result = await asyncio.gather(
        _gemini_classify(text, ml_result),
        _google_nl_moderate(text),
    )

    # Layer 3 — fusion
    final = _fuse_results(ml_result, gemini_result)
    if final is None:
        final = _fallback_result(text, ml_result)

    # Incorporate NL API signal if available
    if nl_result:
        final["layers"]["google_nl"] = nl_result

        # Conservative escalation: if NL API says Toxic, don't downgrade
        category_order = {"Safe": 0, "Risky": 1, "Toxic": 2}
        if category_order.get(nl_result["category"], 0) > category_order.get(final["category"], 0):
            final["category"] = nl_result["category"]
            logger.info(f"[Fusion] NL API escalated to {final['category']}")
    else:
        if "layers" in final:
            final["layers"]["google_nl"] = None

    return final
