# 🛡️ SafeSphere AI — Startup Guide

## Quick Start (2 terminals)

---

### Terminal 1 — Backend (FastAPI)

```powershell
cd "Enliven 3/backend"

# Install Python deps (first time only)
pip install -r requirements.txt

# Add your Gemini API key to .env
# (edit backend/.env — replace YOUR_GEMINI_API_KEY_HERE)

# Start the server
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

---

### Terminal 2 — Frontend (React)

```powershell
cd "Enliven 3/frontend"

# Start the dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 🔑 Get Your Gemini API Key (FREE)

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Open `backend/.env`
5. Replace `YOUR_GEMINI_API_KEY_HERE` with your key
6. Save and restart the backend

---

## 📦 Features Built

| Feature | Status |
|---|---|
| Context-aware AI moderation | ✅ |
| Multilingual (EN/Hindi/Hinglish) | ✅ |
| Explainable AI (why flagged) | ✅ |
| 3-tier classification (Safe/Risky/Toxic) | ✅ |
| Real-time WebSocket live feed | ✅ |
| Moderation dashboard w/ charts | ✅ |
| Alert system (toxic spike) | ✅ |
| Manual input tester | ✅ |
| MongoDB persistence (optional) | ✅ |
| In-memory fallback (no DB needed) | ✅ |

---

## 🏗️ Architecture

```
React (Vite) :5173
    ↕ REST + WebSocket
FastAPI :8000
    ↕ LLM API
Google Gemini 1.5 Flash
    ↕
MongoDB Atlas (optional — in-memory fallback)
```
