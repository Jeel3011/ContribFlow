from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from stage3.enhanced_pipeline import run_enhanced_pipeline

router = APIRouter()

class Stage3Request(BaseModel):
    repo_url: str
    change_description: str
    diff: Optional[str] = ""

@router.post("/stage3/impact")
async def analyze_impact(req: Stage3Request):
    try:
        result = run_enhanced_pipeline(req.repo_url, req.change_description, req.diff)
        return result
    except Exception as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(429, "GitHub rate limit hit. Try again later.")
        raise HTTPException(500, str(e))
