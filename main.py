from fastapi import FastAPI
from stage3.routes import router as stage3_router

app = FastAPI(title="ContribFlow")
app.include_router(stage3_router)

@app.get("/health")
def health():
    return {"status": "ok"}
