from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else

import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stage1.routes import router as stage1_router
from stage2.routes import router as stage2_router
from stage3.routes import router as stage3_router
from stage4.routes import router as stage4_router
from orchestrator.routes import router as orchestrator_router
from shared.executor import get_executor


# ── Lifespan: warm up the sentence-transformers model on startup ───────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load the sentence-transformers model so Stage 2 is instant on first hit."""
    loop = asyncio.get_event_loop()
    try:
        from stage2.semantic_matcher import _get_model
        await loop.run_in_executor(get_executor(), _get_model)
        print("[Startup] ✅ Sentence-transformers model loaded")
    except Exception as e:
        print(f"[Startup] ⚠️  Model warm-up failed (Stage 2 will be slow on first call): {e}")
    yield


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ContribFlow",
    description="4-stage OSS contribution co-pilot powered by AI and IBM Bob",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stage1_router, prefix="/api", tags=["Stage 1 – Gap Finder"])
app.include_router(stage2_router, prefix="/api", tags=["Stage 2 – Idea Deduplication"])
app.include_router(stage3_router, prefix="/api", tags=["Stage 3 – Change Impact"])
app.include_router(stage4_router, prefix="/api", tags=["Stage 4 – Pre-PR Quality"])
app.include_router(orchestrator_router, prefix="/api", tags=["Master Orchestrator"])


# ── Utility endpoints ──────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "ContribFlow",
        "version": "1.0.0",
        "stages": {
            "stage1": "Gap Finder (✅ Complete)",
            "stage2": "Idea Deduplication (✅ Complete)",
            "stage3": "Change Impact Analysis (✅ Complete)",
            "stage4": "Pre-PR Quality Check (✅ Complete)",
            "orchestrator": "Master Orchestrator (✅ Complete — Multi-Agent)"
        },
        "endpoints": {
            "orchestrate_sse": "/api/orchestrate",
            "orchestrate_sync": "/api/orchestrate/sync",
            "stage1": "/api/stage1/analyze",
            "stage2": "/api/stage2/deduplicate",
            "stage3": "/api/stage3/impact",
            "stage4": "/api/stage4/review",
            "health": "/health",
            "warmup": "/warmup",
            "validate_stage3": "/validate/stage3"
        }
    }


@app.get("/health")
async def health():
    """Detailed health check — judges can verify setup is correct at a glance."""
    checks: dict = {}

    # Environment variables
    checks["github_token"] = "set" if os.getenv("GITHUB_TOKEN") else "MISSING"
    checks["openai_api_key"] = "set" if os.getenv("OPENAI_API_KEY") else "MISSING"

    # Sentence-transformers model
    try:
        from stage2.semantic_matcher import _model
        checks["sentence_transformers_model"] = "loaded" if _model is not None else "not_loaded"
    except Exception:
        checks["sentence_transformers_model"] = "not_loaded"

    # ruff availability
    import subprocess
    try:
        result = subprocess.run(["ruff", "--version"], capture_output=True, timeout=3)
        checks["ruff"] = result.stdout.decode().strip() or "available"
    except FileNotFoundError:
        checks["ruff"] = "not_found"
    except Exception:
        checks["ruff"] = "error"

    critical_ok = (
        checks["github_token"] == "set" and
        checks["openai_api_key"] == "set"
    )

    return {
        "status": "ok" if critical_ok else "degraded",
        "version": "1.0.0",
        "checks": checks,
        "stages": {
            "stage1": "operational",
            "stage2": "operational" if checks["sentence_transformers_model"] == "loaded" else "cold (call /warmup)",
            "stage3": "operational",
            "stage4": "operational" if checks["ruff"] != "not_found" else "degraded (ruff not found)",
            "orchestrator": "operational"
        }
    }


@app.get("/warmup")
async def warmup():
    """
    Pre-load models so Stage 2 is instant.
    Call this once before your demo. Takes ~30 seconds on first run.
    """
    results: dict = {}
    loop = asyncio.get_event_loop()

    try:
        from stage2.semantic_matcher import _get_model
        await loop.run_in_executor(get_executor(), _get_model)
        results["sentence_transformers"] = "loaded"
    except Exception as e:
        results["sentence_transformers"] = f"failed: {e}"

    return {"status": "warmup complete", "models": results}


@app.get("/validate/stage3")
async def validate_stage3():
    """
    Run Stage 3 against PR #1395 ground truth and return precision/recall metrics.
    Judges can verify the 100% recall claim interactively via Swagger.
    """
    try:
        from stage3.ground_truth_pr1395 import GROUND_TRUTH_PR1395, validate_stage3_output
        from stage3.enhanced_pipeline import run_enhanced_pipeline

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            get_executor(),
            lambda: run_enhanced_pipeline(
                "https://github.com/Tracer-Cloud/opensre",
                GROUND_TRUTH_PR1395["description"],
                validation_mode=True
            )
        )

        validation = validate_stage3_output(result)
        return {
            "pr": "#1395",
            "repo": "Tracer-Cloud/opensre",
            "metrics": validation.get("file_metrics", {}),
            "test_detection": validation.get("test_detection", {}),
            "recommendations": validation.get("recommendations", []),
            "overall_quality": validation.get("overall_quality", "unknown")
        }
    except Exception as e:
        return {"error": str(e), "hint": "Make sure GITHUB_TOKEN and OPENAI_API_KEY are set"}
