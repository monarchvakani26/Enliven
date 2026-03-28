"""
SafeSphere AI — Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ModerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Text to moderate")


class ModerationResult(BaseModel):
    category: str          # Safe | Risky | Toxic
    type: str              # Hate Speech | Bullying | Threat | Misinformation | None
    confidence: int        # 0–100
    explanation: str
    harmful_phrases: List[str]
    context_analysis: str
    severity: str          # low | medium | high
    language: str          # English | Hindi | Hinglish | Mixed


class ModerationLog(BaseModel):
    id: Optional[str] = None
    text: str
    result: ModerationResult
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "api"    # api | feed | websocket


class ModerateResponse(BaseModel):
    success: bool
    text: str
    result: ModerationResult
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    total_analyzed: int
    safe_count: int
    risky_count: int
    toxic_count: int
    safe_percent: float
    risky_percent: float
    toxic_percent: float
    type_distribution: dict
    language_distribution: dict


class RecentFlaggedResponse(BaseModel):
    logs: List[dict]
    total: int
