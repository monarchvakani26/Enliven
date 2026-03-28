"""
SafeSphere AI — MongoDB Database Layer (async via Motor)
Falls back to in-memory store if MongoDB is not configured.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List

logger = logging.getLogger("safesphere.db")

# ─── In-Memory Fallback ───────────────────────────────────────────────────────
_memory_store: List[dict] = []
_use_memory = False
_db = None

async def connect_db():
    """Initialize MongoDB connection. Falls back to in-memory if URL missing."""
    global _db, _use_memory

    mongo_url = os.getenv("MONGODB_URL", "")
    db_name = os.getenv("MONGODB_DB", "safesphere")

    if not mongo_url or mongo_url.startswith("mongodb+srv://<username>"):
        logger.warning("⚠️  MongoDB URL not configured — using in-memory store.")
        _use_memory = True
        return

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.admin.command("ping")
        _db = client[db_name]
        logger.info(f"✅ MongoDB connected: {db_name}")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed ({e}) — using in-memory store.")
        _use_memory = True


async def insert_log(text: str, result: dict, source: str = "api") -> str:
    """Insert a moderation log entry."""
    doc = {
        "text": text,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }

    if _use_memory:
        doc["_id"] = str(len(_memory_store) + 1)
        _memory_store.append(doc)
        return doc["_id"]

    inserted = await _db.moderation_logs.insert_one(doc)
    return str(inserted.inserted_id)


async def get_stats() -> dict:
    """Compute moderation statistics."""
    if _use_memory:
        logs = _memory_store
    else:
        cursor = _db.moderation_logs.find({})
        logs = await cursor.to_list(length=10000)

    total = len(logs)
    if total == 0:
        return {
            "total_analyzed": 0,
            "safe_count": 0, "risky_count": 0, "toxic_count": 0,
            "safe_percent": 0, "risky_percent": 0, "toxic_percent": 0,
            "type_distribution": {},
            "language_distribution": {},
        }

    safe = sum(1 for l in logs if l["result"]["category"] == "Safe")
    risky = sum(1 for l in logs if l["result"]["category"] == "Risky")
    toxic = sum(1 for l in logs if l["result"]["category"] == "Toxic")

    type_dist: dict = {}
    lang_dist: dict = {}
    for l in logs:
        t = l["result"].get("type", "None")
        lang = l["result"].get("language", "Unknown")
        type_dist[t] = type_dist.get(t, 0) + 1
        lang_dist[lang] = lang_dist.get(lang, 0) + 1

    return {
        "total_analyzed": total,
        "safe_count": safe,
        "risky_count": risky,
        "toxic_count": toxic,
        "safe_percent": round(safe / total * 100, 1),
        "risky_percent": round(risky / total * 100, 1),
        "toxic_percent": round(toxic / total * 100, 1),
        "type_distribution": type_dist,
        "language_distribution": lang_dist,
    }


async def get_recent(n: int = 20, flagged_only: bool = False) -> List[dict]:
    """Return the N most recent moderation logs."""
    if _use_memory:
        logs = list(reversed(_memory_store))
        if flagged_only:
            logs = [l for l in logs if l["result"]["category"] != "Safe"]
        result = logs[:n]
        # Serialize _id
        return [{**l, "_id": l.get("_id", "")} for l in result]

    query = {} if not flagged_only else {"result.category": {"$ne": "Safe"}}
    cursor = _db.moderation_logs.find(query).sort("timestamp", -1).limit(n)
    logs = await cursor.to_list(length=n)
    for l in logs:
        l["_id"] = str(l["_id"])
    return logs
