# Deploying Khan & Associates AI Legal Assistant on Render

This guide provides step-by-step instructions to deploy the AI Legal Assistant as a live web application on **[Render](https://render.com)**.

---

## 🚀 Quick Overview

The repository is pre-configured with:
- **`render.yaml`**: Render Blueprint for one-click setup.
- **`Dockerfile`**: Production container with Tesseract OCR (Urdu), Python 3.12, FastAPI, and pre-built Knowledge Graph indexes.
- **Dynamic Port Support**: Configured to bind automatically to Render's `${PORT:-8000}`.
- **Health Checks**: `/health` endpoint configured for zero-downtime health monitoring.

---

## Step 1: Push Repository to GitHub

If you haven't already pushed your local Git repository to GitHub:

1. Create a new repository on [GitHub](https://github.com/new) (e.g. `AI_Legal_assistant`).
2. Run the following commands in your PowerShell terminal:

```powershell
# Add your GitHub remote (replace with your actual GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/AI_Legal_assistant.git

# Set master branch and push
git branch -M master
git push -u origin master
```

*(Note: `.env`, virtual environments, and large raw dump files are already excluded in `.gitignore` so your push will be fast, secure, and well under GitHub's 100MB limit).*

---

## Step 2: Deploy on Render

### Option A: Using Render Blueprint (Recommended — 1-Click)
1. Log in to your **[Render Dashboard](https://dashboard.render.com)**.
2. Click **New +** (top right) and select **Blueprint**.
3. Connect your GitHub repository (`AI_Legal_assistant`).
4. Render will automatically detect `render.yaml`.
5. Under **Environment Variables**, provide your secret API keys:
   - `GROQ_API_KEY` (starts with `gsk_...`)
   - `GEMINI_API_KEY` (starts with `AQ...` or `AIza...`)
6. Click **Apply**. Render will automatically build the container and deploy your live URL!

---

### Option B: Manual Web Service Setup (Docker)
1. On the **Render Dashboard**, click **New +** ➔ **Web Service**.
2. Select **Build and deploy from a Git repository** and pick `AI_Legal_assistant`.
3. Configure the settings:
   - **Name:** `ai-legal-assistant`
   - **Language / Environment:** `Docker`
   - **Branch:** `master` (or `main`)
   - **Region:** `Oregon (US West)` or nearest to you.
   - **Plan Type:** `Free`
4. Under **Environment Variables**, click **Add Environment Variable**:
   - Key: `GROQ_API_KEY` | Value: `your_groq_api_key_here`
   - Key: `GEMINI_API_KEY` | Value: `your_gemini_api_key_here`
   - Key: `HF_HUB_OFFLINE` | Value: `1`
   - Key: `PYTHONUNBUFFERED` | Value: `1`
5. Click **Create Web Service**.

---

### Option C: Native Python Environment (Alternative)
If you prefer native Python instead of Docker:
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn src.app:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `GROQ_API_KEY`
  - `GEMINI_API_KEY`
  - `HF_HUB_OFFLINE=1`

---

## Step 3: Accessing Your Live Platform

Once the build completes (usually 2–3 minutes), Render will give you a public URL (e.g., `https://ai-legal-assistant.onrender.com`):

1. **Web App:** Visit `https://your-service.onrender.com` to access the full 6-tab legal suite (Research, Review, Compare, Draft, Graph, Upload).
2. **Interactive API Docs:** Visit `https://your-service.onrender.com/docs` to view Swagger UI.
3. **Health Check:** `https://your-service.onrender.com/health` returns `{"status": "HEALTHY"}`.

---

## 💡 Free Tier Tips on Render
- **Cold Starts:** Free instances on Render spin down after 15 minutes of inactivity. The first request after sleep may take ~30 seconds to wake up.
- **Memory Footprint:** Our API is optimized to consume only ~70MB of RAM, running comfortably within Render's 512MB free tier limit.

