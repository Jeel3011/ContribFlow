"""
FastAPI routes for Stage 4 (Pre-PR Quality Check)
Handles HTTP endpoints for code review before PR submission
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from stage4.pipeline import run_stage4


router = APIRouter()


class Stage4Request(BaseModel):
    """Request model for Stage 4 quality check endpoint"""
    repo_url: str
    diff: str
    bob_response: Optional[str] = None


@router.post("/stage4/review")
async def review_changes(req: Stage4Request):
    """
    Perform pre-PR quality check on git diff
    
    Args:
        req: Stage4Request containing repo_url, diff, and optional bob_response
        
    Returns:
        JSON response with:
        - repo: Repository identifier
        - passes_check: Boolean indicating if checks pass (None if no bob_response)
        - summary: Summary of issues found
        - issues: List of issues with severity, file, line, description, and fix
        - prompt_for_bob: Prompt to copy to Bob IDE
        - metadata: Pipeline execution metadata
        
    Raises:
        HTTPException: 400 for invalid input, 429 for rate limits, 500 for other errors
    """
    # Validate input
    if not req.diff or not req.diff.strip():
        raise HTTPException(400, "Diff cannot be empty")
    
    if not req.repo_url or not req.repo_url.strip():
        raise HTTPException(400, "Repository URL cannot be empty")
    
    # Validate repo URL format
    if "github.com" not in req.repo_url:
        raise HTTPException(400, "Invalid GitHub repository URL")
    
    try:
        result = run_stage4(req.repo_url, req.diff, req.bob_response)
        return result
    except Exception as e:
        error_msg = str(e).lower()
        
        if "rate limit" in error_msg:
            raise HTTPException(429, "GitHub rate limit hit. Try again later.")
        
        if "not found" in error_msg or "404" in error_msg:
            raise HTTPException(404, "Repository not found or not accessible")
        
        # Generic error
        raise HTTPException(500, f"Pipeline error: {str(e)}")


# Made with Bob