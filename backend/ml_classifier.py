"""
SafeSphere AI — ML Classifier
Trains and runs a local TF-IDF + Logistic Regression model.
This is Layer 1 of the 3-layer moderation pipeline.
"""
import os
import json
import logging
import joblib
import numpy as np
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report
from training_data import TRAINING_DATA, LABEL_NAMES

logger = logging.getLogger("safesphere.ml")

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "safesphere_classifier.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

# ─── Build Pipeline ───────────────────────────────────────────────────────────
def build_pipeline() -> Pipeline:
    """
    TF-IDF + Logistic Regression pipeline.
    - char_wb n-grams (1-4): handles multilingual text, slang, typos
    - word n-grams (1-2): captures phrase-level patterns
    - L2-regularized LR: stable, interpretable, fast
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=20000,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight="balanced",
            solver="lbfgs",
            multi_class="auto",
        )),
    ])


# ─── Train ────────────────────────────────────────────────────────────────────
def train() -> dict:
    """Train and persist the classifier. Returns metrics dict."""
    MODEL_DIR.mkdir(exist_ok=True)

    texts = [t for t, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]

    logger.info(f"Training on {len(texts)} examples ({labels.count(0)} Safe, {labels.count(1)} Risky, {labels.count(2)} Toxic)")

    pipeline = build_pipeline()

    # Cross-validation accuracy
    cv_scores = cross_val_score(pipeline, texts, labels, cv=5, scoring="accuracy")
    logger.info(f"5-fold CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Train on full dataset
    pipeline.fit(texts, labels)

    # Per-class metrics
    preds = pipeline.predict(texts)
    report = classification_report(labels, preds, target_names=["Safe", "Risky", "Toxic"], output_dict=True)

    metrics = {
        "training_examples": len(texts),
        "cv_accuracy_mean": round(float(cv_scores.mean()), 4),
        "cv_accuracy_std": round(float(cv_scores.std()), 4),
        "training_accuracy": round(float(report["accuracy"]), 4),
        "per_class": {
            cls: {
                "precision": round(report[cls]["precision"], 3),
                "recall": round(report[cls]["recall"], 3),
                "f1": round(report[cls]["f1-score"], 3),
            }
            for cls in ["Safe", "Risky", "Toxic"]
        },
        "model_type": "TF-IDF (char 2-4 ngrams) + Logistic Regression",
        "features": 20000,
    }

    # Persist
    joblib.dump(pipeline, MODEL_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"✅ Model saved to {MODEL_PATH}")
    logger.info(f"   Training accuracy : {metrics['training_accuracy']:.1%}")
    logger.info(f"   CV accuracy       : {metrics['cv_accuracy_mean']:.1%} ± {metrics['cv_accuracy_std']:.1%}")

    return metrics


# ─── Load ─────────────────────────────────────────────────────────────────────
_pipeline: Pipeline | None = None
_metrics: dict = {}

def load() -> bool:
    """Load the trained pipeline from disk. Returns True if successful."""
    global _pipeline, _metrics
    if MODEL_PATH.exists():
        try:
            _pipeline = joblib.load(MODEL_PATH)
            if METRICS_PATH.exists():
                with open(METRICS_PATH) as f:
                    _metrics = json.load(f)
            logger.info(f"✅ ML model loaded (CV acc: {_metrics.get('cv_accuracy_mean', '?'):.1%})")
            return True
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
    return False


def get_metrics() -> dict:
    return _metrics


# ─── Predict ──────────────────────────────────────────────────────────────────
def predict(text: str) -> dict:
    """
    Run inference. Returns:
    {
      "category": "Safe" | "Risky" | "Toxic",
      "confidence": 0-100,
      "probabilities": {"Safe": float, "Risky": float, "Toxic": float}
    }
    """
    if _pipeline is None:
        return {"category": "Risky", "confidence": 50, "probabilities": {"Safe": 0.33, "Risky": 0.34, "Toxic": 0.33}}

    probs = _pipeline.predict_proba([text])[0]
    idx = int(np.argmax(probs))
    category = LABEL_NAMES[idx]
    confidence = int(round(float(probs[idx]) * 100))

    return {
        "category": category,
        "confidence": confidence,
        "probabilities": {
            "Safe": round(float(probs[0]), 4),
            "Risky": round(float(probs[1]), 4),
            "Toxic": round(float(probs[2]), 4),
        }
    }


# ─── Init (train if not found) ────────────────────────────────────────────────
def init():
    """Load existing model or train from scratch."""
    if not load():
        logger.info("No pretrained model found — training now...")
        train()
        load()
