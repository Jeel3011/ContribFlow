"""
FastAPI routes for the Master Orchestrator
Single endpoint: POST /api/orchestrate — streams SSE events
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class OrchestrateRequest(BaseModel):
    repo_url: str
    user_idea: str
    diff: Optional[str] = ""
    workflow_mode: Optional[str] = "full"  # "full" | "impact_only"


@router.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    """
    Master orchestrator endpoint — runs all applicable stages autonomously.

    Streams Server-Sent Events (SSE) in real-time so the UI can show
    per-stage progress as the agents work.

    Event types:
    - orchestrator_start   — pipeline is beginning
    - stage_start          — a specific stage has started
    - stage_complete       — a specific stage finished with results
    - stage_skipped        — a stage was skipped (e.g. Stage 4 with no diff)
    - stage_error          — a stage encountered an error
    - orchestrator_stop    — pipeline stopped early (e.g. conflict found)
    - orchestrator_complete — all stages done, summary card available
    - stream_end           — final event with all stage data
    """
    if not req.repo_url or "github.com" not in req.repo_url:
        raise HTTPException(400, "Valid GitHub repository URL required")

    if not req.user_idea or not req.user_idea.strip():
        raise HTTPException(400, "user_idea is required")

    if req.workflow_mode not in ("full", "impact_only"):
        raise HTTPException(400, "workflow_mode must be 'full' or 'impact_only'")

    async def event_stream():
        try:
            from orchestrator.graph import stream_orchestrator
            async for event_json in stream_orchestrator(
                repo_url=req.repo_url,
                user_idea=req.user_idea,
                diff=req.diff or "",
                workflow_mode=req.workflow_mode
            ):
                yield f"data: {event_json}\n\n"
        except Exception as e:
            error_event = json.dumps({
                "type": "fatal_error",
                "message": str(e)
            })
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/orchestrate/sync")
async def orchestrate_sync(req: OrchestrateRequest):
    """
    Non-streaming version of the orchestrator.
    Returns all stage results in a single JSON response.
    Useful for testing and for clients that don't support SSE.
    """
    if not req.repo_url or "github.com" not in req.repo_url:
        raise HTTPException(400, "Valid GitHub repository URL required")

    try:
        from orchestrator.graph import run_orchestrator_sync
        final_state = run_orchestrator_sync(
            repo_url=req.repo_url,
            user_idea=req.user_idea,
            diff=req.diff or "",
            workflow_mode=req.workflow_mode
        )
        return {
            "stage1": final_state.get("stage1_result"),
            "stage2": final_state.get("stage2_result"),
            "stage3": final_state.get("stage3_result"),
            "stage4": final_state.get("stage4_result"),
            "summary": next(
                (e for e in reversed(final_state.get("events", [])) if e.get("type") == "orchestrator_complete"),
                {}
            ).get("summary"),
            "events": final_state.get("events", [])
        }
    except Exception as e:
        if "rate limit" in str(e).lower():
            raise HTTPException(429, "GitHub rate limit hit. Try again later.")
        raise HTTPException(500, str(e))


# Made with Bob
