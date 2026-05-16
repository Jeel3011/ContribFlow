"""
FastAPI routes for Stage 2 (Idea Deduplication)
Handles HTTP endpoints for contribution idea conflict detection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from stage2.pipeline import run_stage2


router = APIRouter()


class Stage2Request(BaseModel):
    """Request model for Stage 2 deduplication endpoint"""
    repo_url: str
    idea: str


@router.post("/stage2/deduplicate")
async def deduplicate_idea(req: Stage2Request):
    """
    Check if a contribution idea conflicts with existing GitHub issues/PRs
    
    Args:
        req: Stage2Request containing repo_url and idea
        
    Returns:
        JSON response with semantic matches and Bob prompt
        
    Raises:
        HTTPException: 429 for rate limits, 500 for other errors
    """
    try:
        result = run_stage2(req.repo_url, req.idea)
        return result
    except Exception as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(429, "GitHub rate limit hit. Try again later.")
        raise HTTPException(500, str(e))

# Made with Bob
