# 🛡️ SafeSphere AI — Context-Aware Content Moderation Engine

> **Real-time, multilingual, AI-powered content moderation for social platforms.**
> Built for hackathons. Production-ready architecture.

---

## 🏗️ Architecture — Multi-Layer AI Pipeline

```
                        User Content
                             │
              ┌──────────────▼──────────────┐
              │        LAYER 1 (Always On)   │
              │  Trained ML Model            │
              │  TF-IDF (char n-grams)       │
              │  + Logistic Regression       │
              │  Trained on 115+ examples    │
              │  EN / Hindi / Hinglish       │
              └──────────┬──────────────────┘
                         │ instant, offline
              ┌───────────▼──────────────────────────────┐
              │          LAYER 2 (Concurrent)             │
              │                                           │
              │  2a: Google Gemini 2.0 Flash (LLM)        │
              │     • Context-aware classification         │
              │     • Sarcasm & intent detection           │
              │     • Full multilingual support            │
              │     • Human-readable explanations          │
              │                                           │
              │  2b: Google Cloud NL API [optional]       │
              │     • moderateText endpoint                │
              │     • Google's trained safety model        │
              │     • Signals: TOXIC, INSULT, HATE...     │
              │     • Free: 5,000 units/month              │
              └──────────────┬────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │         LAYER 3             │
              │     Confidence Fusion       │
              │  Gemini 70% + ML 30%        │
              │  NL API escalation guard    │
              └──────────────┬──────────────┘
                             │
                    Final Verdict
              Safe | Risky | Toxic + Explanation
```

### Why 3 layers?

| Layer | Technology | Role | Always On? |
|-------|-----------|------|-----------|
| 1 | scikit-learn TF-IDF + LR | Fast baseline, offline, no quota | ✅ Yes |
| 2a | Google Gemini 2.0 Flash | Deep context, multilingual, explainability | ⚡ When online |
| 2b | Google Cloud NL API | Google's safety model, structured scores | 🔑 Needs key |
| 3 | Confidence Fusion | Weighted combination + escalation guard | ✅ Always |

---

## 🚀 Features

- 🧠 **3-Layer AI Pipeline** — trained ML model + Gemini LLM + Google NL API
- 📡 **Live Moderation Feed** — real-time WebSocket stream with color-coded cards
- 📊 **Analytics Dashboard** — ML model metrics, charts, per-class F1 scores
- 🔍 **Input Tester** — paste any text and get full layer-by-layer breakdown
- 🌐 **Multilingual** — English, Hindi, Hinglish, mixed text
- 🎯 **Explainability** — explains WHY content is Safe/Risky/Toxic
- ⚡ **Smart Fallback** — works offline with ML-only when APIs unavailable

---

## 🤖 ML Model Details

| Property | Value |
|----------|-------|
| Algorithm | Logistic Regression (lbfgs, L2) |
| Features | TF-IDF, char n-grams (2-4), 20K features |
| Training set | 115 multilingual examples |
| Classes | Safe (0), Risky (1), Toxic (2) |
| CV Accuracy | ~57% (5-fold, small dataset) |
| Train Accuracy | 100% |
| Languages | English, Hindi, Hinglish |

> CV accuracy is lower because the dataset is small (115 examples). In production, accuracy improves significantly with more data. The model is **always augmented by Gemini** for final verdict.

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — REST API + WebSocket server
- **scikit-learn** — ML model (TF-IDF + Logistic Regression)
- **google-genai** — Google Gemini 2.0 Flash SDK
- **motor** — Async MongoDB driver (in-memory fallback included)
- **Python 3.11+**

### Frontend
- **React + Vite** — Fast SPA
- **Chart.js** — Analytics charts
- **WebSocket** — Real-time live feed

### Google Services Used (Free Tier)
| Service | Use | Free Tier |
|---------|-----|-----------|
| Gemini 2.0 Flash | LLM contextual analysis | 15 RPM / 1M tokens/day |
| Cloud NL API (optional) | Content safety model | 5,000 units/month |

---

## ⚡ Quick Start

### 1. Clone & setup
```bash
git clone https://github.com/your-username/safesphere-ai.git
cd safesphere-ai
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt

# Copy env and add your key
cp .env.example .env
# Edit .env: add GEMINI_API_KEY from https://aistudio.google.com/app/apikey

# Train the ML model
python train_and_test.py

# Start server
uvicorn main:app --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Open
```
http://localhost:5173
```

---

## 📁 Project Structure

```
safesphere-ai/
├── backend/
│   ├── main.py              # FastAPI app, REST + WebSocket
│   ├── moderator.py         # 3-layer AI pipeline
│   ├── ml_classifier.py     # Trained ML model (inference)
│   ├── training_data.py     # Curated multilingual dataset
│   ├── train_and_test.py    # Training script with metrics
│   ├── database.py          # MongoDB + in-memory store
│   ├── models.py            # Pydantic schemas
│   ├── sample_comments.py   # Sample dataset for live feed
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── LiveFeedPage.jsx   # Real-time WebSocket feed
│       │   ├── DashboardPage.jsx  # Analytics + ML model metrics
│       │   └── TesterPage.jsx     # Manual input + layer breakdown
│       ├── components/
│       │   ├── ModerationCard.jsx # Result card with layer view
│       │   └── AlertBanner.jsx    # Toxic spike alerts
│       └── App.jsx
└── README.md
```

---

## 🌐 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/moderate` | Moderate a text (full 3-layer pipeline) |
| GET | `/api/stats` | Aggregated moderation statistics |
| GET | `/api/recent` | Recent moderation logs |
| GET | `/api/ml-metrics` | Trained ML model performance metrics |
| WS | `/ws/feed` | Live moderation feed stream |

---

## 🔑 Environment Variables

```env
# Required
GEMINI_API_KEY=...        # From https://aistudio.google.com/app/apikey

# Optional — enables Google NL API layer
GOOGLE_NL_API_KEY=...     # From https://console.cloud.google.com

# Optional — for persistent storage
MONGODB_URL=...            # From https://cloud.mongodb.com (free tier)

FRONTEND_URL=http://localhost:5173
```

---

## 📊 Classification Categories

| Category | Description | Example |
|----------|-------------|---------|
| ✅ Safe | No harmful intent | *"You're killing it! Great work!"* |
| ⚠️ Risky | Ambiguous, sarcastic, or possibly harmful | *"Oh wow, nice job genius 🙄"* |
| 🚫 Toxic | Clear harmful intent | *"I will find you and make you pay"* |

### Harmful Content Types
- Hate Speech
- Bullying / Harassment
- Threat / Violence
- Misinformation

---

## 🌍 Multilingual Support

| Language | Example |
|----------|---------|
| English | *"Go kill yourself, nobody wants you here"* |
| Hindi | *"Tu bewakoof hai, akal nahi hai teri"* |
| Hinglish | *"Ek baar aur kiya toh I swear main chup nahi rahunga"* |
| Mixed | Auto-detected and classified |

---

*Built with ❤️ for hackathon — SafeSphere AI*
