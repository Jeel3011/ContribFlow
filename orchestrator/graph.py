"""
ContribFlow Master Orchestrator
LangGraph StateGraph that coordinates all 4 specialist agents autonomously.
Single entry point: POST /api/orchestrate (SSE streaming)
"""

import json
import asyncio
import logging
from typing import TypedDict, Literal, AsyncIterator
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


# ─── Orchestrator State ───────────────────────────────────────────────────────

class OrchestratorState(TypedDict):
    # User inputs
    repo_url: str
    owner_repo: str
    user_idea: str          # Plain-English contribution idea
    diff: str               # Optional git diff (for Stage 4)
    workflow_mode: str      # "full" | "impact_only"

    # Stage outputs (populated as agents complete)
    stage1_result: dict
    stage2_result: dict
    stage3_result: dict
    stage4_result: dict

    # Orchestration tracking
    current_stage: str      # "idle" | "stage1" | "stage2" | "stage3" | "stage4" | "done"
    events: list            # Accumulated SSE events
    error: str              # Error message if any stage fails
    stop_reason: str        # Why we stopped ("done" | "conflict" | "error")


# ─── Agent Nodes ─────────────────────────────────────────────────────────────

def route_node(state: OrchestratorState) -> OrchestratorState:
    """Entry node: determines which stages to run based on workflow_mode"""
    logger.info(f"Orchestrator routing: mode={state['workflow_mode']}")
    state["events"].append({
        "type": "orchestrator_start",
        "workflow_mode": state["workflow_mode"],
        "repo": state["owner_repo"],
        "message": f"ContribFlow orchestrator starting in '{state['workflow_mode']}' mode..."
    })
    return state


def stage1_node(state: OrchestratorState) -> OrchestratorState:
    """Gap Finder Agent"""
    state["current_stage"] = "stage1"
    state["events"].append({
        "type": "stage_start",
        "stage": "stage1",
        "stage_name": "Gap Finder",
        "message": "Agent is scanning repository for contribution gaps..."
    })

    try:
        from stage1.pipeline import run_stage1
        result = run_stage1(state["repo_url"])
        state["stage1_result"] = result
        gap_count = len(result.get("gaps", []))
        state["events"].append({
            "type": "stage_complete",
            "stage": "stage1",
            "stage_name": "Gap Finder",
            "summary": f"Found {gap_count} contribution {'gap' if gap_count == 1 else 'gaps'}",
            "data": result
        })
        logger.info(f"Stage 1 complete: {gap_count} gaps found")
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        state["error"] = f"Stage 1 (Gap Finder) failed: {str(e)}"
        state["events"].append({
            "type": "stage_error",
            "stage": "stage1",
            "message": str(e)
        })

    return state


def stage2_node(state: OrchestratorState) -> OrchestratorState:
    """Idea Deduplication Agent"""
    state["current_stage"] = "stage2"
    state["events"].append({
        "type": "stage_start",
        "stage": "stage2",
        "stage_name": "Idea Deduplication",
        "message": "Agent is checking for conflicts with existing issues and PRs..."
    })

    try:
        from stage2.pipeline import run_stage2
        result = run_stage2(state["repo_url"], state["user_idea"])
        state["stage2_result"] = result

        status = result.get("status", "clear")
        conflict_count = len(result.get("conflicts", []))

        state["events"].append({
            "type": "stage_complete",
            "stage": "stage2",
            "stage_name": "Idea Deduplication",
            "summary": f"Status: {status.upper()} — {conflict_count} conflict(s) found" if conflict_count else f"Status: {status.upper()} — No conflicts",
            "data": result
        })

        # If hard conflict, stop the pipeline
        if status == "conflict" and conflict_count > 0:
            state["stop_reason"] = "conflict"
            state["events"].append({
                "type": "orchestrator_stop",
                "reason": "conflict",
                "message": f"Pipeline stopped: your idea conflicts with existing work. {result.get('recommendation_text', '')}"
            })

        logger.info(f"Stage 2 complete: status={status}")
    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")
        state["error"] = f"Stage 2 (Dedup) failed: {str(e)}"
        state["events"].append({
            "type": "stage_error",
            "stage": "stage2",
            "message": str(e)
        })

    return state


def stage3_node(state: OrchestratorState) -> OrchestratorState:
    """Change Impact Analysis Agent"""
    state["current_stage"] = "stage3"
    state["events"].append({
        "type": "stage_start",
        "stage": "stage3",
        "stage_name": "Change Impact Analysis",
        "message": "Agent is mapping dependencies and calculating blast radius..."
    })

    try:
        from stage3.enhanced_pipeline import run_enhanced_pipeline
        result = run_enhanced_pipeline(
            repo_url=state["repo_url"],
            change_description=state["user_idea"],
            diff=state.get("diff", "")
        )
        state["stage3_result"] = result

        affected_count = len(result.get("files_affected", []))
        state["events"].append({
            "type": "stage_complete",
            "stage": "stage3",
            "stage_name": "Change Impact Analysis",
            "summary": f"{affected_count} files affected, {len(result.get('services_at_risk', []))} services at risk",
            "data": result
        })
        logger.info(f"Stage 3 complete: {affected_count} files affected")
    except Exception as e:
        logger.error(f"Stage 3 failed: {e}")
        state["error"] = f"Stage 3 (Impact) failed: {str(e)}"
        state["events"].append({
            "type": "stage_error",
            "stage": "stage3",
            "message": str(e)
        })

    return state


def stage4_node(state: OrchestratorState) -> OrchestratorState:
    """Pre-PR Quality Check Agent"""
    state["current_stage"] = "stage4"

    if not state.get("diff", "").strip():
        state["events"].append({
            "type": "stage_skipped",
            "stage": "stage4",
            "stage_name": "Pre-PR Quality Check",
            "message": "Skipped: no git diff provided. Paste a diff to run the quality check."
        })
        return state

    state["events"].append({
        "type": "stage_start",
        "stage": "stage4",
        "stage_name": "Pre-PR Quality Check",
        "message": "Agent is reviewing your diff for code quality issues..."
    })

    try:
        from stage4.pipeline import run_stage4
        result = run_stage4(state["repo_url"], state["diff"])
        state["stage4_result"] = result

        passes = result.get("passes_check", None)
        issue_count = len(result.get("issues", []))
        state["events"].append({
            "type": "stage_complete",
            "stage": "stage4",
            "stage_name": "Pre-PR Quality Check",
            "summary": ("✅ Passes check" if passes else "❌ Fails check") + f" — {issue_count} issue(s) found",
            "data": result
        })
        logger.info(f"Stage 4 complete: passes={passes}, issues={issue_count}")
    except Exception as e:
        logger.error(f"Stage 4 failed: {e}")
        state["error"] = f"Stage 4 (Pre-PR) failed: {str(e)}"
        state["events"].append({
            "type": "stage_error",
            "stage": "stage4",
            "message": str(e)
        })

    return state


def finalize_node(state: OrchestratorState) -> OrchestratorState:
    """Builds the final consolidated report"""
    state["current_stage"] = "done"

    # Build overall readiness score (0–100)
    score = 100
    if state.get("stage2_result", {}).get("status") == "complementary":
        score -= 10
    issues = state.get("stage4_result", {}).get("issues", [])
    errors = sum(1 for i in issues if i.get("severity") == "error")
    warnings = sum(1 for i in issues if i.get("severity") == "warning")
    score -= errors * 15
    score -= warnings * 5
    score = max(0, min(100, score))

    summary = {
        "overall_score": score,
        "uniqueness": state.get("stage2_result", {}).get("status", "not_checked"),
        "impact_scope": {
            "files": len(state.get("stage3_result", {}).get("files_affected", [])),
            "services": len(state.get("stage3_result", {}).get("services_at_risk", [])),
        },
        "code_quality": {
            "passes": state.get("stage4_result", {}).get("passes_check"),
            "errors": errors,
            "warnings": warnings,
        },
        "top_gap": state.get("stage1_result", {}).get("gaps", [{}])[0].get("title", "N/A")
                   if state.get("stage1_result", {}).get("gaps") else "N/A",
        "stop_reason": state.get("stop_reason", "done")
    }

    state["events"].append({
        "type": "orchestrator_complete",
        "summary": summary,
        "message": f"Analysis complete. Contribution readiness score: {score}/100"
    })

    return state


# ─── Conditional Routing ─────────────────────────────────────────────────────

def route_after_route(state: OrchestratorState) -> Literal["stage1", "stage3"]:
    """Skip Stage 1 & 2 in impact_only mode"""
    if state["workflow_mode"] == "impact_only":
        return "stage3"
    return "stage1"


def route_after_stage2(state: OrchestratorState) -> Literal["stage3", "finalize"]:
    """Stop pipeline if hard conflict found"""
    if state.get("stop_reason") == "conflict":
        return "finalize"
    return "stage3"


def route_after_stage3(state: OrchestratorState) -> Literal["stage4", "finalize"]:
    """Go to Stage 4 only if diff provided"""
    if state.get("diff", "").strip():
        return "stage4"
    return "finalize"


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def create_orchestrator_graph() -> StateGraph:
    """Build and compile the master orchestrator StateGraph"""
    workflow = StateGraph(OrchestratorState)

    # Nodes
    workflow.add_node("route", route_node)
    workflow.add_node("stage1", stage1_node)
    workflow.add_node("stage2", stage2_node)
    workflow.add_node("stage3", stage3_node)
    workflow.add_node("stage4", stage4_node)
    workflow.add_node("finalize", finalize_node)

    # Entry → route
    workflow.set_entry_point("route")

    # route → stage1 OR stage3 (impact_only)
    workflow.add_conditional_edges("route", route_after_route, {
        "stage1": "stage1",
        "stage3": "stage3"
    })

    # stage1 → stage2 (always in full mode)
    workflow.add_edge("stage1", "stage2")

    # stage2 → stage3 OR finalize (if conflict)
    workflow.add_conditional_edges("stage2", route_after_stage2, {
        "stage3": "stage3",
        "finalize": "finalize"
    })

    # stage3 → stage4 (if diff) OR finalize
    workflow.add_conditional_edges("stage3", route_after_stage3, {
        "stage4": "stage4",
        "finalize": "finalize"
    })

    # stage4 → finalize
    workflow.add_edge("stage4", "finalize")

    # finalize → END
    workflow.add_edge("finalize", END)

    return workflow.compile()


# ─── Main Execution Entry Points ──────────────────────────────────────────────

def run_orchestrator_sync(
    repo_url: str,
    user_idea: str,
    diff: str = "",
    workflow_mode: str = "full"
) -> dict:
    """
    Synchronous orchestrator execution.
    Returns the full final state including all stage results and events.
    """
    owner_repo = repo_url.replace("https://github.com/", "").strip("/")

    initial_state: OrchestratorState = {
        "repo_url": repo_url,
        "owner_repo": owner_repo,
        "user_idea": user_idea,
        "diff": diff,
        "workflow_mode": workflow_mode,
        "stage1_result": {},
        "stage2_result": {},
        "stage3_result": {},
        "stage4_result": {},
        "current_stage": "idle",
        "events": [],
        "error": "",
        "stop_reason": ""
    }

    graph = create_orchestrator_graph()
    final_state = graph.invoke(initial_state)
    return final_state


async def stream_orchestrator(
    repo_url: str,
    user_idea: str,
    diff: str = "",
    workflow_mode: str = "full"
) -> AsyncIterator[str]:
    """
    Async generator that yields SSE-formatted events as the orchestrator runs.
    Streams each stage's events as they complete.
    """
    loop = asyncio.get_event_loop()

    # Run synchronously in thread pool to avoid blocking
    final_state = await loop.run_in_executor(
        None,
        run_orchestrator_sync,
        repo_url, user_idea, diff, workflow_mode
    )

    # Yield all accumulated events
    for event in final_state.get("events", []):
        yield json.dumps(event)

    # Final done signal
    yield json.dumps({"type": "stream_end", "final_state": {
        "stage1": final_state.get("stage1_result"),
        "stage2": final_state.get("stage2_result"),
        "stage3": final_state.get("stage3_result"),
        "stage4": final_state.get("stage4_result"),
    }})


# Made with Bob
