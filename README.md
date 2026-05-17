<div align="center">

# ⚡ ContribFlow

### *Your AI-Powered OSS Contribution Co-Pilot*

[![Built for IBM Bob Hackathon](https://img.shields.io/badge/IBM%20Bob%20Hackathon-2026-0062ff?style=for-the-badge&logo=ibm&logoColor=white)](https://github.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestrated-4A154B?style=for-the-badge)](https://github.com/langchain-ai/langgraph)

**ContribFlow takes you from "I want to contribute to this repo" → "Perfect PR, ready to merge" in 4 automated stages.**

[🚀 Quick Start](#-quick-start-5-minutes) • [🧠 How It Works](#-how-it-works) • [🛠️ Full Setup](#️-full-setup) • [🎯 Demo Repos](#-demo-repositories) • [🔧 Troubleshooting](#-troubleshooting)

---

</div>

## 🧠 How It Works

ContribFlow orchestrates **4 specialized AI agents** in a LangGraph pipeline. Each stage is fully autonomous — just paste a GitHub repo URL and describe your idea.

```
GitHub Repo URL
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Gap Finder          Find the best place to contribute │
│  → Scores file suspiciousness before LLM to save API tokens     │
│  → Returns: gaps[], impact scores, line ranges                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Idea Deduplication  Has someone already started this? │
│  → Semantic embeddings + LLM verification (threshold ≥ 0.85)    │
│  → Filters wontfix/rejected issues before comparison            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Change Impact Analysis   Map the blast radius ✦ CORE  │
│  → GitHub Code Search + static dependency graph                  │
│  → Explainable confidence traces (direct/indirect/dynamic)       │
│  → Validated against opensre/tracer-cloud PR #1395               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Pre-PR Quality Check  Catch issues before CI does     │
│  → Ruff static linting (async, non-blocking)                     │
│  → LLM convention review against repo's existing patterns        │
│  → Returns: issues[], severity, fix suggestions, passes_check    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    Contribution Readiness Score /100
```

---

## 🚀 Quick Start (5 Minutes)



### What You Need

| Requirement | Version | Where to get it |
|-------------|---------|-----------------|
| Python | 3.10+ | [python.org](https://python.org/downloads) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| GitHub Token | — | [github.com/settings/tokens](https://github.com/settings/tokens) → *Generate new token (classic)* → check `public_repo` |
| OpenAI API Key | — | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

> **Check your versions first:**
> ```bash
> python3 --version   # needs 3.10+
> node --version      # needs 18+
> ```

---

### Step 1 — Clone the Repo

```bash
git clone https://github.com/<your-username>/ContribFlow.git
cd ContribFlow
```

---

### Step 2 — Set Up Your Keys

```bash
# Copy the example env file
cp .env.example .env
```

Now open `.env` in any text editor and fill in your keys:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 **GitHub Token scopes needed:** `public_repo` (for public repos) or `repo` (for private repos)

---

### Step 3 — Start the Backend

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # Mac/Linux
# OR
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Verify it's alive: open **http://localhost:8000/health** in your browser → you should see `"status": "ok"`.

---

### Step 4 — Start the Frontend

Open a **new terminal tab** (keep the backend running):

```bash
# Navigate to the frontend folder
cd frontend

# Install Node packages
npm install

# Start the dev server
npm run dev
```

You should see:
```
  VITE v8.x  ready in XXX ms

  ➜  Local:   http://localhost:8501/
```

> If port 8501 is taken, Vite will try **8502**, **8503**, etc. — check your terminal for the actual URL.

---

### Step 5 — Use It! 🎉

1. Open the URL shown in your terminal (e.g. `http://localhost:8501`)
2. Paste any GitHub repo URL in the top bar, e.g.:
   ```
   https://github.com/opensre/tracer-cloud
   ```
3. Hit the **✦ Auto-Pilot** tab → describe your contribution idea → click **🚀 Run Analysis**
4. Watch all 4 stages run in real-time with live logs

---

## 🛠️ Full Setup

### One-Shot Start Scripts

If you just want to start everything with one command:

**Mac/Linux:**
```bash
chmod +x start.sh && ./start.sh
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Windows (Command Prompt):**
```cmd
start.bat
```

---

### Running Stages Individually

You can also use each stage as a standalone REST API:

```bash
# Stage 1: Find gaps in a repo
curl -X POST http://localhost:8000/api/stage1/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/psf/requests", "focus_area": "error-handling"}'

# Stage 2: Check if your idea is already proposed
curl -X POST http://localhost:8000/api/stage2/deduplicate \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/psf/requests", "idea": "Add retry with exponential backoff"}'

# Stage 3: Blast radius analysis
curl -X POST http://localhost:8000/api/stage3/impact \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/opensre/tracer-cloud", "change_description": "Modify retry logic in http_client"}'

# Stage 4: Pre-PR code review
curl -X POST http://localhost:8000/api/stage4/review \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/psf/requests", "diff": "your git diff here"}'

# Run all 4 stages (orchestrated, SSE stream)
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/opensre/tracer-cloud", "user_idea": "Add retry logic", "diff": "", "workflow_mode": "full"}'
```

Full interactive API docs: **http://localhost:8000/docs**

---

## 🎯 Demo Repositories

These repos work great for testing all 4 stages:

| Repository | Why it's good |
|---|---|
| `opensre/tracer-cloud` | **Ground truth** — Stage 3 validates against PR #1395 |
| `psf/requests` | Small, well-structured, lots of open issues |
| `pallets/flask` | Popular, active, good for Stage 2 dedup testing |
| `tiangolo/fastapi` | Large enough to show real blast radius in Stage 3 |

---

## 🏗️ Project Structure

```
ContribFlow/
├── main.py                    # FastAPI entrypoint (lifespan warmup, /health, /validate)
├── requirements.txt           # Python dependencies
├── .env.example               # Copy this to .env and fill your keys
├── DEMO_CHECKLIST.md          # Pre-demo 30-min checklist
│
├── stage1/                    # Gap Finder Agent
│   ├── routes.py              # POST /api/stage1/analyze
│   ├── suspiciousness_scorer.py  # Pre-LLM heuristic scoring
│   └── github_api.py
│
├── stage2/                    # Idea Deduplication Agent
│   ├── routes.py              # POST /api/stage2/deduplicate
│   ├── pipeline.py            # Semantic embedding + LLM verification
│   ├── semantic_matcher.py    # sentence-transformers embeddings
│   └── github_api.py          # Filters wontfix/rejected issues
│
├── stage3/                    # Change Impact Agent ✦ (Core Stage)
│   ├── routes.py              # POST /api/stage3/impact
│   ├── enhanced_pipeline.py   # LangGraph ReAct agent + GitHub Code Search
│   └── github_search.py       # Async-safe rate-limit handling
│
├── stage4/                    # Pre-PR Quality Agent
│   ├── routes.py              # POST /api/stage4/review
│   ├── static_checker.py      # Async ruff linting (non-blocking)
│   ├── convention_sampler.py  # Samples similar files for style baseline
│   └── response_parser.py
│
├── orchestrator/              # Master LangGraph pipeline
│   ├── routes.py              # POST /api/orchestrate (SSE stream)
│   └── graph.py               # Full 4-stage StateGraph
│
├── shared/                    # Shared utilities
│   ├── executor.py            # ThreadPoolExecutor (shared across all routes)
│   └── errors.py              # Standardized HTTP error mapper
│
└── frontend/                  # React + Vite UI
    ├── src/App.jsx             # Main UI (1400+ lines, all 4 stages + orchestrator)
    ├── src/main.jsx
    ├── index.html
    └── vite.config.js         # Runs on port 8501
```

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000        # Mac/Linux
netstat -ano | findstr :8000   # Windows

# Kill whatever's on port 8000
kill -9 $(lsof -t -i:8000)   # Mac/Linux
```

**`ModuleNotFoundError`?**
```bash
# Make sure your venv is activated
source venv/bin/activate   # you should see (venv) in your prompt
pip install -r requirements.txt
```

**`OPENAI_API_KEY not set`?**
```bash
cat .env   # make sure it has your key, no quotes needed
```

---

### Frontend won't start

```bash
# Make sure you're in the frontend folder
cd frontend

# Reinstall dependencies
rm -rf node_modules && npm install

# Start again
npm run dev
```

**Port already in use?** Vite auto-increments — check your terminal for the actual URL (it'll say `http://localhost:8502` or similar).

---

### Stage 3 returns empty results

- This stage uses **GitHub Code Search API** which has stricter rate limits
- Make sure your `GITHUB_TOKEN` has `public_repo` scope
- Try with a smaller repo first (`psf/requests` works well)
- Wait 60 seconds if you see a 403 error (rate limit resets)

### UI shows "Agent is reasoning…" forever

- The backend may have crashed — check your backend terminal for errors
- Hit **http://localhost:8000/health** — if it's down, restart the backend
- The `/warmup` endpoint pre-loads sentence-transformers: `GET http://localhost:8000/warmup`

---

## 📊 API Health Check

```bash
# Full health status
curl http://localhost:8000/health

# Pre-warm sentence-transformers (do this before a demo!)
curl http://localhost:8000/warmup

# Validate Stage 3 against ground truth
curl http://localhost:8000/validate/stage3
```

---

## 🧪 Architecture Decisions

| Decision | Why |
|---|---|
| **Non-blocking ruff** via `asyncio.create_subprocess_exec` | `subprocess.run()` blocks the event loop — catastrophic under concurrent load |
| **Shared `ThreadPoolExecutor(8)`** | Prevents spinning up N executors per request; all routes share one pool |
| **`RateLimitException` instead of `time.sleep()`** | `sleep()` in a thread blocks async scheduling; exception lets the caller handle backoff |
| **Pre-scoring before LLM (Stage 1)** | Cuts LLM token cost by ~80%; only top 5 suspicious files go to the model |
| **Semantic threshold 0.85** | 0.7 caused too many false conflict flags; 0.85 drops false positives significantly |
| **Workflow toggle inside Orchestrator tab** | Putting it in the nav bar caused React re-render + navigation conflicts |

---

## 🏆 IBM Bob Hackathon

- **Event:** May 15–17, 2026
- **Validation target:** `opensre/tracer-cloud` PR #1395
- **Bob sessions:** exported to `/bob-sessions/` (required for judging)
- **Token budget:** 40 Bobcoins/account × 4 members = 160 Bobcoins total

---

<div align="center">

Built with ❤️ for the **IBM Bob Hackathon 2026**

*ContribFlow — because every good contribution starts with knowing where to begin.*

</div>
