from fastapi import FastAPI
from stage1.routes import router as stage1_router
from stage2.routes import router as stage2_router
from stage3.routes import router as stage3_router
from stage4.routes import router as stage4_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ContribFlow",
    description="4-stage OSS contribution co-pilot powered by AI",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all stage routers
app.include_router(stage1_router, prefix="/api", tags=["Stage 1"])
app.include_router(stage2_router, prefix="/api", tags=["Stage 2"])
app.include_router(stage3_router, prefix="/api", tags=["Stage 3"])
app.include_router(stage4_router, prefix="/api", tags=["Stage 4"])

@app.get("/")
def root():
    return {
        "name": "ContribFlow",
        "version": "1.0.0",
        "stages": {
            "stage1": "Gap Finder (✅ Complete)",
            "stage2": "Idea Deduplication (✅ Complete)",
            "stage3": "Change Impact Analysis (✅ Complete)",
            "stage4": "Pre-PR Quality Check (✅ Complete)"
        },
        "endpoints": {
            "stage1": "/api/stage1/analyze",
            "stage2": "/api/stage2/deduplicate",
            "stage3": "/api/stage3/impact",
            "stage4": "/api/stage4/review"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "stages": {
            "stage1": "operational",
            "stage2": "operational",
            "stage3": "operational",
            "stage4": "operational"
        }
    }
