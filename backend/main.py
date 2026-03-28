"""
SafeSphere AI — FastAPI Application
REST API + WebSocket real-time feed
"""
import os
import asyncio
import random
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from models import ModerateRequest, ModerateResponse, StatsResponse
from moderator import moderate
from database import connect_db, insert_log, get_stats, get_recent
from sample_comments import SAMPLE_COMMENTS

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger("safesphere")

# ─── Active WebSocket connections ─────────────────────────────────────────────
active_connections: List[WebSocket] = []

# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SafeSphere AI starting up...")
    # Init ML model (train from scratch if not found)
    import ml_classifier
    ml_classifier.init()
    await connect_db()
    yield
    logger.info("👋 SafeSphere AI shutting down.")

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SafeSphere AI",
    description="Real-time context-aware content moderation engine",
    version="1.0.0",
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "SafeSphere AI", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/moderate", response_model=ModerateResponse)
async def moderate_text(request: ModerateRequest):
    """Moderate a single text input using the AI engine."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.info(f"Moderating: {text[:60]}...")
    result = await moderate(text)

    # Persist to DB
    await insert_log(text, result, source="api")

    return ModerateResponse(
        success=True,
        text=text,
        result=result,
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/api/stats")
async def get_dashboard_stats():
    """Return aggregated moderation statistics for the dashboard."""
    stats = await get_stats()
    return stats


@app.get("/api/recent")
async def get_recent_logs(n: int = 20, flagged_only: bool = False):
    """Return the N most recent moderation logs."""
    logs = await get_recent(n=n, flagged_only=flagged_only)
    return {"logs": logs, "total": len(logs)}


@app.get("/api/feed/sample")
async def get_sample_comments():
    """Return the sample comment dataset for frontend reference."""
    return {"comments": SAMPLE_COMMENTS}


@app.get("/api/ml-metrics")
async def get_ml_metrics():
    """Return trained ML model performance metrics."""
    import ml_classifier
    metrics = ml_classifier.get_metrics()
    return {
        "model_type": metrics.get("model_type", "TF-IDF + Logistic Regression"),
        "training_examples": metrics.get("training_examples", 0),
        "cv_accuracy": metrics.get("cv_accuracy_mean", 0),
        "cv_std": metrics.get("cv_accuracy_std", 0),
        "training_accuracy": metrics.get("training_accuracy", 0),
        "per_class": metrics.get("per_class", {}),
        "features": metrics.get("features", 0),
        "pipeline": "Layer 1: TF-IDF+LR → Layer 2: Gemini 2.0 Flash → Layer 2b: Google NL API → Layer 3: Confidence Fusion",
    }


@app.post("/api/retrain")
async def retrain_model():
    """
    Retrain the ML classifier from scratch.
    Returns updated metrics after training.
    Useful for demoing live model updates.
    """
    import ml_classifier
    import asyncio
    loop = asyncio.get_event_loop()
    # Run in thread to avoid blocking event loop
    metrics = await loop.run_in_executor(None, ml_classifier.train)
    ml_classifier.load()
    logger.info(f"✅ Model retrained: CV={metrics['cv_accuracy_mean']:.1%}")
    return {
        "success": True,
        "message": "Model retrained successfully",
        "metrics": {
            "training_examples": metrics["training_examples"],
            "cv_accuracy": metrics["cv_accuracy_mean"],
            "training_accuracy": metrics["training_accuracy"],
            "per_class": metrics["per_class"],
        }
    }


@app.get("/api/system-status")
async def system_status():
    """Full system health — all AI layers status."""
    import ml_classifier
    ml_metrics = ml_classifier.get_metrics()
    gemini_key = bool(os.getenv("GEMINI_API_KEY"))

    try:
        from langdetect import detect
        lang_ok = True
    except ImportError:
        lang_ok = False

    return {
        "status": "ok",
        "layers": {
            "layer1_ml": {
                "status": "active" if ml_metrics else "not_loaded",
                "model": ml_metrics.get("model_type", ""),
                "cv_accuracy": ml_metrics.get("cv_accuracy_mean", 0),
                "training_examples": ml_metrics.get("training_examples", 0),
                "cost": "free",
            },
            "layer2_gemini": {
                "status": "configured" if gemini_key else "missing_key",
                "model": "gemini-2.0-flash",
                "key_set": gemini_key,
                "cost": "free (15 RPM)",
            },
            "layer3_langdetect": {
                "status": "active" if lang_ok else "not_installed",
                "description": "Google language detection algorithm",
                "languages": ["English", "Hindi", "Hinglish", "Mixed"],
                "cost": "free",
            },
            "layer4_fusion": {
                "status": "active",
                "strategy": "Gemini 70% + ML 30% weighted",
                "cost": "free",
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── WebSocket Live Feed ──────────────────────────────────────────────────────

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """
    Stream live moderated comments to the frontend.
    Uses pre-classified results for the live feed demo to preserve
    Gemini API quota for the Input Tester use case.
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connected. Active: {len(active_connections)}")

    try:
        # Send a welcome ping
        await websocket.send_json({
            "type": "connected",
            "message": "SafeSphere AI live feed connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Pre-classified results for reliable live feed demo
        # Covers all categories and languages for visual impact
        FEED_DATA = [
            {"text": "You're absolutely killing it on this project 🔥", "result": {"category": "Safe", "type": "None", "confidence": 97, "explanation": "Positive slang expressing admiration. No harmful intent.", "harmful_phrases": [], "context_analysis": "Idiomatic expression 'killing it' used positively.", "severity": "low", "language": "English"}},
            {"text": "I will find you and make you pay for this.", "result": {"category": "Toxic", "type": "Threat / Violence", "confidence": 96, "explanation": "Direct personal threat implying violent retribution.", "harmful_phrases": ["I will find you", "make you pay"], "context_analysis": "Clear threatening intent toward a specific person.", "severity": "high", "language": "English"}},
            {"text": "Tu bewakoof hai, akal nahi hai teri.", "result": {"category": "Toxic", "type": "Bullying / Harassment", "confidence": 91, "explanation": "Hindi insult calling someone foolish and unintelligent.", "harmful_phrases": ["bewakoof", "akal nahi hai"], "context_analysis": "Direct personal insult in Hindi targeting intelligence.", "severity": "medium", "language": "Hindi"}},
            {"text": "Great work everyone, the team really pulled through!", "result": {"category": "Safe", "type": "None", "confidence": 99, "explanation": "Positive team appreciation with no harmful elements.", "harmful_phrases": [], "context_analysis": "Sincere encouragement and praise for collective achievement.", "severity": "low", "language": "English"}},
            {"text": "Oh wow, nice job genius. You've really outdone yourself 🙄", "result": {"category": "Risky", "type": "None", "confidence": 72, "explanation": "Sarcastic tone suggests mockery but intent depends on context.", "harmful_phrases": ["nice job genius"], "context_analysis": "Sarcasm detected via emoji and tone. Could be playful or demeaning.", "severity": "low", "language": "English"}},
            {"text": "The vaccines contain microchips to track you!", "result": {"category": "Toxic", "type": "Misinformation", "confidence": 98, "explanation": "Dangerous health misinformation with no scientific basis.", "harmful_phrases": ["vaccines contain microchips"], "context_analysis": "Conspiracy theory that can cause vaccine hesitancy and public harm.", "severity": "high", "language": "English"}},
            {"text": "Yaar aaj ka din bahut acha tha, maza aa gaya!", "result": {"category": "Safe", "type": "None", "confidence": 99, "explanation": "Casual Hindi expression of having a great day.", "harmful_phrases": [], "context_analysis": "Friendly, positive sentiment with no harmful content.", "severity": "low", "language": "Hindi"}},
            {"text": "Some people just shouldn't be allowed on the internet.", "result": {"category": "Risky", "type": "None", "confidence": 65, "explanation": "Vague exclusionary statement that could target any group.", "harmful_phrases": ["shouldn't be allowed"], "context_analysis": "Ambiguous — could be frustration or coded exclusion.", "severity": "medium", "language": "English"}},
            {"text": "All [religion] people shouldn't be in our country.", "result": {"category": "Toxic", "type": "Hate Speech", "confidence": 99, "explanation": "Calls for religious-based exclusion — clear hate speech.", "harmful_phrases": ["shouldn't be in our country"], "context_analysis": "Discriminatory statement targeting a religious group.", "severity": "high", "language": "English"}},
            {"text": "Bhai tune toh kamaal kar diya aaj! Proud of you!", "result": {"category": "Safe", "type": "None", "confidence": 98, "explanation": "Warm bilingual compliment expressing pride.", "harmful_phrases": [], "context_analysis": "Genuine praise using Hindi-English mix (Hinglish). Positive.", "severity": "low", "language": "Hinglish"}},
            {"text": "Go kill yourself, nobody wants you here.", "result": {"category": "Toxic", "type": "Bullying / Harassment", "confidence": 99, "explanation": "Extremely dangerous message encouraging self-harm.", "harmful_phrases": ["Go kill yourself", "nobody wants you"], "context_analysis": "Severe cyberbullying with potential to cause real harm.", "severity": "high", "language": "English"}},
            {"text": "Keep talking and I'll destroy your career.", "result": {"category": "Toxic", "type": "Threat / Violence", "confidence": 93, "explanation": "Implied professional threat meant to silence or intimidate.", "harmful_phrases": ["I'll destroy your career"], "context_analysis": "Coercive threat using professional consequences as leverage.", "severity": "high", "language": "English"}},
            {"text": "5G towers were designed to spread the virus, share this!", "result": {"category": "Toxic", "type": "Misinformation", "confidence": 97, "explanation": "Debunked conspiracy linking 5G to viral spread.", "harmful_phrases": ["5G towers were designed to spread the virus"], "context_analysis": "Dangerous misinformation encouraging viral sharing of false claims.", "severity": "high", "language": "English"}},
            {"text": "Ek baar aur kiya toh I swear main chup nahi rahunga.", "result": {"category": "Risky", "type": "None", "confidence": 68, "explanation": "Hinglish warning that could be a threat or frustrated venting.", "harmful_phrases": ["chup nahi rahunga"], "context_analysis": "Ambiguous — 'I won't stay silent' can mean standing up or escalating.", "severity": "medium", "language": "Hinglish"}},
            {"text": "Women don't belong in tech, they ruin everything.", "result": {"category": "Toxic", "type": "Hate Speech", "confidence": 97, "explanation": "Discriminatory statement targeting women in professional settings.", "harmful_phrases": ["don't belong in tech", "they ruin everything"], "context_analysis": "Gender-based hate speech undermining women's professional presence.", "severity": "high", "language": "English"}},
            {"text": "Congratulations on the promotion, totally deserved! 🎉", "result": {"category": "Safe", "type": "None", "confidence": 99, "explanation": "Sincere professional congratulations.", "harmful_phrases": [], "context_analysis": "Celebratory message with no negative undertones.", "severity": "low", "language": "English"}},
            {"text": "Yeh toh bilkul gadha hai, kuch samajh nahi aata isko.", "result": {"category": "Toxic", "type": "Bullying / Harassment", "confidence": 89, "explanation": "Hindi insult comparing person to a donkey (gadha = donkey).", "harmful_phrases": ["gadha hai", "kuch samajh nahi"], "context_analysis": "Animal-based insult in Hindi implying stupidity.", "severity": "medium", "language": "Hindi"}},
            {"text": "Bro this movie is literally fire, must watch karo!", "result": {"category": "Safe", "type": "None", "confidence": 99, "explanation": "Enthusiastic recommendation using slang 'fire' positively.", "harmful_phrases": [], "context_analysis": "Hinglish slang expressing excitement. No harmful intent.", "severity": "low", "language": "Hinglish"}},
        ]

        random.shuffle(FEED_DATA)
        idx = 0

        while True:
            item = FEED_DATA[idx % len(FEED_DATA)]
            idx += 1

            text = item["text"]
            result = item["result"]

            # Save to DB for dashboard stats
            await insert_log(text, result, source="feed")

            payload = {
                "type": "moderation",
                "id": f"feed-{idx}",
                "text": text,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_json(payload)
            logger.info(f"[Feed] → {result['category']} | {text[:45]}...")

            # 4–7s interval: fast enough to feel live, not spammy
            await asyncio.sleep(random.uniform(4.0, 7.0))

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

