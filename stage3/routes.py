"""
FastAPI routes for Stage 3 (Change Impact Analysis)
"""

import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from shared.executor import get_executor
from shared.errors import handle_pipeline_error

router = APIRouter()


class Stage3Request(BaseModel):
    repo_url: str
    change_description: str
    diff: Optional[str] = ""
    validation_mode: Optional[bool] = False  # Explicit flag for PR #1395 validation


@router.post("/stage3/impact")
async def analyze_impact(req: Stage3Request):
    """
    Analyze the blast radius of a proposed code change.

    Use validation_mode=true when testing against Tracer-Cloud/opensre PR #1395.
    """
    try:
        from stage3.enhanced_pipeline import run_enhanced_pipeline
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            get_executor(),
            lambda: run_enhanced_pipeline(
                req.repo_url,
                req.change_description,
                req.diff or "",
                req.validation_mode or False
            )
        )
        return result
    except Exception as e:
        raise handle_pipeline_error(e, "stage3")
