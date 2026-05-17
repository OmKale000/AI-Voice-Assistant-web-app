# 💠 AI ELITE Voice Assistant (V4)

AI Voice Assistant web app is a production-grade AI platform engineered for high performance, persistence, and premium user experience. It transcends basic prototypes by implementing enterprise-level caching, multi-modal failover, and a modern SaaS interface.

## 🌟 V4 "Elite" Highlights

- **Firebase Persistence:** Conversations are now permanently stored in Firestore, allowing session recovery and chat history browsing.
- **Smart Response Flow:** Intelligent caching layer with query fingerprinting to reuse responses for repeated queries, saving thousands of tokens.
- **Premium Glassmorphism UI:** A completely redesigned frontend with animated orbs, dark-mode gradients, and a professional sidebar.
- **Observability Dashboard:** Real-time analytics on latency, stability, provider health, and request volume.
- **Concurrency Protection:** Multi-layer guards to prevent duplicate processing, repeated submissions, and auto-resubmission loops.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit (Custom CSS/HTML)
- **Database:** Firebase Firestore
- **AI Engine:** Groq (Primary) + Google Gemini (Fallback)
- **Voice:** Whisper V3 (STT) + Edge-TTS (TTS)
- **Caching:** Cachetools (TTL Caching)

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- [Firebase Service Account Key](https://console.firebase.google.com/) (Save as `firebase-key.json` in root)
- API Keys for Groq, Gemini, and OpenWeatherMap.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
GROQ_API_KEY=...
GEMINI_API_KEY=...
FIREBASE_CREDENTIALS_PATH=firebase-key.json
WEATHER_API_KEY=...
```

---

## 📊 Analytics & Monitoring

- **Active Monitoring:** View system stability and provider failover rates in the sidebar.
- **Session History:** Browse and reload previous conversations instantly.
- **Live Health:** Green pulse indicates high-speed Groq availability; amber indicates Gemini fallback active.

---

## 🛡️ Engineering Excellence

- **Query Deduplication:** Prevents redundant processing of identical voice inputs.
- **Memory Trimming:** Sliding-window context management to optimize LLM attention.
- **Async Logging:** Non-blocking Firebase writes to keep request latency low.
- **MIME Validation:** Strict file-type enforcement for audio uploads.

