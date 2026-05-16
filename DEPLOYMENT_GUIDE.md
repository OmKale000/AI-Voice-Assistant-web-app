# 🚀 NEXUS AI Deployment Guide

NEXUS AI is designed to be deployment-ready. Follow these steps to host your assistant.

## 🐳 Docker Setup Steps (Local or Server)
Docker ensures the app runs the same way everywhere.

1.  **Install Docker**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux).
2.  **Prepare Environment**: Ensure your `.env` file is in the root directory.
3.  **Build and Start**: Open a terminal in the project root and run:
    ```bash
    docker-compose up -d --build
    ```
4.  **Verify**: 
    - Frontend: `http://localhost:8501`
    - Backend: `http://localhost:8000/health`
5.  **Stop**: `docker-compose down`

---

## ☁️ Cloud Deployment Steps (e.g., Render / Railway)

### Step 1: Push to GitHub
1. Create a new private repository on GitHub.
2. Initialize and push your code:
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

### Step 2: Configure Hosting (Render Example)
1. **New Web Service**: Connect your GitHub repo.
2. **Build Settings**:
   - Runtime: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0`
3. **Environment Variables**: Add all keys from your `.env` (GROQ, GEMINI, etc.).
4. **Deploy**: Click "Deploy Web Service".

---

## 🔒 Firebase Security
1. Go to Google Cloud Console.
2. Ensure your Service Account has "Firebase Admin" permissions.
3. If using Docker on a server, mount your `firebase-key.json` safely or use an environment variable to store the JSON string.

---
**NEXUS AI V4 Elite** | Designed for Stability and Scale.

