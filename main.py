from fastapi import FastAPI
from stage2.routes import router as stage2_router
from stage3.routes import router as stage3_router
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

# Include Stage 2 and Stage 3 routers
app.include_router(stage2_router, prefix="/api", tags=["Stage 2"])
app.include_router(stage3_router, prefix="/api", tags=["Stage 3"])

@app.get("/")
def root():
    return {
        "name": "ContribFlow",
        "version": "1.0.0",
        "stages": {
            "stage1": "Gap Finder (Not implemented)",
            "stage2": "Idea Deduplication (✅ Complete)",
            "stage3": "Change Impact Analysis (✅ Complete)",
            "stage4": "Pre-PR Quality Check (Not implemented)"
        },
        "endpoints": {
            "stage2": "/api/stage2/deduplicate",
            "stage3": "/api/stage3/impact"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "stage3": "operational"}
