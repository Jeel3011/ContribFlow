from fastapi import FastAPI
from stage2.routes import router as stage2_router
from stage3.routes import router as stage3_router

app = FastAPI(title="ContribFlow")
app.include_router(stage2_router, prefix="/api")
app.include_router(stage3_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
