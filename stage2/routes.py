"""
FastAPI routes for Stage 2 (Idea Deduplication)
Handles HTTP endpoints for contribution idea conflict detection
"""

import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from shared.executor import get_executor
from shared.errors import handle_pipeline_error

router = APIRouter()


class Stage2Request(BaseModel):
    """Request model for Stage 2 deduplication endpoint"""
    repo_url: str
    idea: str


@router.post("/stage2/deduplicate")
async def deduplicate_idea(req: Stage2Request):
    """
    Check if a contribution idea conflicts with existing GitHub issues/PRs.

    Returns semantic matches and a recommendation.
    """
    try:
        from stage2.pipeline import run_stage2
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            get_executor(),
            lambda: run_stage2(req.repo_url, req.idea)
        )
        return result
    except Exception as e:
        raise handle_pipeline_error(e, "stage2")

# Made with Bob
