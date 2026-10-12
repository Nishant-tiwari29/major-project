# Render Deployment Guide
## Intelligent Logistics & Vehicle Routing Optimizer 2.0

This guide explains how to deploy the full-stack Logistics Optimizer on [Render](https://render.com) for free.

---

## Deployment Architectures

You can deploy the platform in either of two ways:

1. **Option A: Unified Full-Stack Service (Recommended)**
   - Single Render Web Service hosting both the FastAPI backend and the React GIS frontend.
   - **Advantages:** Zero CORS configuration, uses only 1 free service on Render's free tier, single URL for everything.
2. **Option B: Decoupled Multi-Service (Static Site + Web Service)**
   - Frontend deployed as a Render **Static Site**.
   - Backend deployed as a Render **Web Service**.
3. **Option C: Docker Container Deployment**
   - Built and deployed automatically via the included [`Dockerfile`](file:///c:/Users/Nishant%20Tiwari/OneDrive/Desktop/major-project/Dockerfile).

---

## Step 1: Push Code to GitHub

1. Initialize git and commit all project files:
   ```bash
   cd major-project
   git init
   git add .
   git commit -m "Initial commit: Intelligent Logistics & Vehicle Routing Optimizer 2.0"
   ```
2. Create a new repository on [GitHub](https://github.com/new).
3. Push to your repository:
   ```bash
   git remote add origin https://github.com/<your-username>/major-project.git
   git branch -M main
   git push -u origin main
   ```

---

## Method 1: Automatic Blueprint Deploy (Easiest)

Render includes native Blueprint support via [`render.yaml`](file:///c:/Users/Nishant%20Tiwari/OneDrive/Desktop/major-project/render.yaml):

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** &rarr; Select **Blueprint**.
3. Connect your GitHub repository (`major-project`).
4. Render will automatically detect `render.yaml` and configure:
   - Service name: `logistics-optimizer-fullstack`
   - Build command: `./render-build.sh`
   - Start command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - Health check: `/health`
5. Click **Apply**.
6. Render will build and deploy your project automatically!

---

## Method 2: Manual Web Service Setup (Step-by-Step)

If you prefer configuring through the Render Web UI:

### 1. Create Web Service
1. In the Render Dashboard, click **New +** &rarr; **Web Service**.
2. Select your `major-project` GitHub repository.
3. Configure settings:
   - **Name:** `logistics-optimizer-2`
   - **Region:** Any (e.g., Oregon, Ohio, Frankfurt)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank)*
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r backend/requirements.txt && cd frontend && npm install && npm run build && cd .. && python backend/app/core/seed_data.py && python backend/app/ml/model_trainer.py
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type:** `Free`

### 2. Configure Environment Variables
Under the **Environment Variables** section, add:
| Key | Value | Description |
|---|---|---|
| `PYTHONPATH` | `backend` | Ensures Python resolves `app.` imports |
| `PYTHON_VERSION` | `3.11.9` | Sets matching Python runtime version |
| `CORS_ORIGINS` | `*` | Allows cross-origin API access |

### 3. Click "Create Web Service"
Render will:
- Install backend dependencies.
- Compile the React frontend into `frontend/dist/`.
- Seed the SQLite database with depots, vehicles, and orders.
- Train the ML traffic prediction model ($R^2 = 97.3\%$).
- Launch the Uvicorn web server.

---

## Method 3: Containerized Docker Deployment

Render natively supports Docker builds:

1. In Render Dashboard, click **New +** &rarr; **Web Service**.
2. Connect your repository.
3. Set **Runtime** to **Docker**.
4. Render will automatically detect the multi-stage [`Dockerfile`](file:///c:/Users/Nishant%20Tiwari/OneDrive/Desktop/major-project/Dockerfile) in the repository root.
5. Click **Create Web Service**.

---

## Verifying the Live Deployment

Once the build completes (showing `Your service is live 🎉`), open your Render URL (e.g., `https://logistics-optimizer-2.onrender.com`):

1. **Web Dashboard:** The interactive Leaflet route map will load directly at the root URL `/`.
2. **Swagger API Docs:** Accessible at `/docs`.
3. **Health Check:** Accessible at `/health` returning `{"status": "healthy"}`.
4. **Interactive Algorithms:**
   - Click **Execute Optimization Engine** to compute routes with Branch & Bound or Held-Karp Bitmask DP.
   - Switch to **DP State Table** to inspect live memoization states.
   - Switch to **What-If Simulator** to test fuel prices, traffic congestion, and road closures.
   - Switch to **Algorithm Benchmarks** to view empirical runtimes and the 0.0% optimality gap.

---

## Troubleshooting Common Render Issues

### Issue 1: "Port binding error" or "Application didn't respond to health check"
- **Cause:** Hardcoding port 8000 instead of listening to Render's assigned `$PORT`.
- **Solution:** Our start command uses `--port $PORT` and binds to `0.0.0.0`, which dynamically adheres to Render's environment.

### Issue 2: "ModuleNotFoundError: No module named 'app'"
- **Cause:** Missing `PYTHONPATH`.
- **Solution:** Set `PYTHONPATH=backend` in the Render Environment Variables tab.

### Issue 3: "Database connection failed"
- **Solution:** By default, the application runs on SQLite (`logistics.db`). If you connect a Render Managed PostgreSQL database, Render automatically injects `DATABASE_URL`, which our [`backend/app/core/config.py`](file:///c:/Users/Nishant%20Tiwari/OneDrive/Desktop/major-project/backend/app/core/config.py) automatically converts to `postgresql+asyncpg://`.
