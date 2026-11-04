# 🚀 Step-by-Step Guide: Deploying ShopKaro AI Platform on Render

This guide walks you through deploying the complete **ShopKaro AI Commerce Intelligence Platform** (FastAPI backend + DuckDB database + interactive Customer/Operations/Management dashboard) to **[Render.com](https://render.com)**.

---

## 📋 Prerequisites
1. A GitHub account.
2. A free Render account at [render.com](https://render.com).
3. Your local repository pushed to a GitHub repository.

---

## ⚡ Option 1: Docker Deployment (Recommended — 1-Click)
Deploying via Docker is the most reliable approach because our [`Dockerfile`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/Dockerfile) packages the exact Python 3.12 environment, pre-compiled C libraries (for DuckDB, LightGBM, and Torch), and static dashboard assets.

### Steps:
1. Log in to your **[Render Dashboard](https://dashboard.render.com/)**.
2. Click **"New +"** in the top navigation and select **"Web Service"**.
3. Choose **"Build and deploy from a Git repository"** and click **Next**.
4. Connect your GitHub account and select your `AI_E-Commerce_Intelligence_Platform` repository.
5. In the configuration settings:
   * **Name:** `shopkaro-ai-platform` (or any name you prefer)
   * **Region:** Select the region closest to you (e.g., *Frankfurt*, *Oregon*, or *Singapore*)
   * **Branch:** `main` (or `master`)
   * **Runtime:** Select **`Docker`** *(Render will automatically detect `Dockerfile`)*
   * **Instance Type:** 
     * **Starter ($7/mo - Recommended):** Provides 1 GB RAM, perfect for 50,000 SKU BM25 indexing and real-time machine learning inference.
     * **Free:** Works for basic testing (512 MB RAM).
6. Under **Advanced Settings**:
   * **Health Check Path:** Enter `/health`
7. Click **"Create Web Service"**.

Render will now build the Docker image, run the health check, and deploy your live platform!

---

## 🐍 Option 2: Native Python Deployment (Alternative)
If you prefer not to use Docker:

1. Follow steps 1–4 above.
2. In the configuration settings:
   * **Runtime:** Select **`Python 3`**
   * **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   * **Start Command:**
     ```bash
     uvicorn src.serving.api:app --host 0.0.0.0 --port $PORT
     ```
3. Add Environment Variable:
   * `PYTHON_VERSION`: `3.12.0`
4. Set **Health Check Path** to `/health`.
5. Click **"Create Web Service"**.

---

## 🌐 Accessing Your Live Platform

Once Render displays the green **"Live"** status (usually 2–3 minutes):

1. **Interactive Dashboard:**
   * URL: `https://your-service-name.onrender.com/`
   * Opens the full single-page application with:
     * **🛍️ Customer View:** Personalized homepage, UrduLish search, grounded AI assistant chat.
     * **🏭 Operations View:** 14-day demand forecasts, stockout alerts, overstock markdown tables.
     * **📊 Management View:** Executive KPIs, RFM personas, A/B test results (+21.1% CVR lift).
2. **Interactive API Documentation (Swagger UI):**
   * URL: `https://your-service-name.onrender.com/docs`
   * Allows live testing of all 10 endpoints directly in your browser.
3. **Health Check:**
   * URL: `https://your-service-name.onrender.com/health`

---

## 💡 Important Cloud Tips
* **No Hardcoded URLs:** Our frontend in [`dashboard/app.js`](file:///c:/Users/MEE/Anti-Gravity_projects/AI_E-Commerce_Intelligence_Platform/dashboard/app.js) uses `window.location.origin` dynamically, meaning it will automatically bind to your `.onrender.com` domain with zero manual configuration.
* **Database Included:** The 80 MB DuckDB database (`data/processed/shopkaro.duckdb`) is under GitHub's 100 MB per-file threshold and will be pushed directly with your git repo.
* **Auto-Deploy on Git Push:** Every time you push updates to GitHub, Render will automatically rebuild and deploy the new version with zero downtime.

