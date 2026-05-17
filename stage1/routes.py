"""
FastAPI routes for Stage 1 (Gap Finder)
Handles HTTP endpoints for repository gap analysis
"""

import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from shared.executor import get_executor
from shared.errors import handle_pipeline_error

router = APIRouter()


class Stage1Request(BaseModel):
    """Request model for Stage 1 gap analysis endpoint"""
    repo_url: str
    bob_response: Optional[str] = None


@router.post("/stage1/analyze")
async def analyze_gaps(req: Stage1Request):
    """
    Analyze a GitHub repository to identify contribution gaps.

    Returns JSON with gaps list and prompt_for_bob.
    """
    try:
        from stage1.pipeline import run_stage1
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            get_executor(),
            lambda: run_stage1(req.repo_url, req.bob_response)
        )
        return result
    except Exception as e:
        raise handle_pipeline_error(e, "stage1")

# Made with Bob