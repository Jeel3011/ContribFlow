"""
FastAPI routes for Stage 4 (Pre-PR Quality Check)
Handles HTTP endpoints for code review before PR submission
"""

import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.executor import get_executor
from shared.errors import handle_pipeline_error

router = APIRouter()


class Stage4Request(BaseModel):
    """Request model for Stage 4 quality check endpoint"""
    repo_url: str
    diff: str
    bob_response: Optional[str] = None


@router.post("/stage4/review")
async def review_changes(req: Stage4Request):
    """
    Perform pre-PR quality check on git diff.

    Returns issues by severity with a pass/fail result.
    """
    if not req.diff or not req.diff.strip():
        raise HTTPException(400, "Diff cannot be empty")

    if not req.repo_url or not req.repo_url.strip():
        raise HTTPException(400, "Repository URL cannot be empty")

    if "github.com" not in req.repo_url:
        raise HTTPException(400, "Invalid GitHub repository URL")

    try:
        from stage4.pipeline import run_stage4
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            get_executor(),
            lambda: run_stage4(req.repo_url, req.diff, req.bob_response)
        )
        return result
    except Exception as e:
        raise handle_pipeline_error(e, "stage4")

# Made with Bob