"""
FastAPI routes for Stage 1 (Gap Finder)
Handles HTTP endpoints for repository gap analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from stage1.pipeline import run_stage1


router = APIRouter()


class Stage1Request(BaseModel):
    """Request model for Stage 1 gap analysis endpoint"""
    repo_url: str
    bob_response: Optional[str] = None


@router.post("/stage1/analyze")
async def analyze_gaps(req: Stage1Request):
    """
    Analyze a GitHub repository to identify contribution gaps
    
    Args:
        req: Stage1Request containing repo_url and optional bob_response
        
    Returns:
        JSON response with:
        - repo: Repository identifier
        - gaps: List of identified gaps (empty if no bob_response)
        - prompt_for_bob: Prompt to copy to Bob IDE
        - metadata: Pipeline execution metadata
        
    Raises:
        HTTPException: 429 for rate limits, 500 for other errors
    """
    try:
        result = run_stage1(req.repo_url, req.bob_response)
        return result
    except Exception as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(429, "GitHub rate limit hit. Try again later.")
        raise HTTPException(500, str(e))


# Made with Bob