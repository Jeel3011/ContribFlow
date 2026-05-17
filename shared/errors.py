"""
Standardized error handling for all ContribFlow pipeline routes.
Prevents raw exception messages from leaking to API consumers.
"""
from fastapi import HTTPException


def handle_pipeline_error(e: Exception, stage: str) -> HTTPException:
    """
    Map a pipeline exception to a structured FastAPI HTTPException.

    Args:
        e: The exception raised by the pipeline
        stage: Stage identifier (e.g. "stage1", "stage3")

    Returns:
        HTTPException with a structured detail dict
    """
    error_str = str(e).lower()

    if "rate limit" in error_str or "403" in error_str:
        return HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": "GitHub rate limit hit. Wait 60 seconds and try again.",
                "stage": stage
            }
        )
    if "authentication" in error_str or "401" in error_str:
        return HTTPException(
            status_code=401,
            detail={
                "code": "AUTH_ERROR",
                "message": "GitHub token invalid or expired.",
                "stage": stage
            }
        )
    if "not found" in error_str or "404" in error_str:
        return HTTPException(
            status_code=404,
            detail={
                "code": "REPO_NOT_FOUND",
                "message": "Repository not found or is private.",
                "stage": stage
            }
        )
    if "openai" in error_str or "api key" in error_str:
        return HTTPException(
            status_code=503,
            detail={
                "code": "LLM_UNAVAILABLE",
                "message": "OpenAI API unavailable. Check OPENAI_API_KEY.",
                "stage": stage
            }
        )

    # Generic — don't leak the raw exception message
    return HTTPException(
        status_code=500,
        detail={
            "code": "PIPELINE_ERROR",
            "message": "Internal pipeline error. Check server logs.",
            "stage": stage
        }
    )
