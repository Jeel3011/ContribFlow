"""
Pipeline orchestrator for Stage 4 (Pre-PR Quality Check)
Coordinates diff parsing, static checks, convention sampling, and Bob integration
"""

from typing import Optional
from stage4.diff_parser import parse_diff, get_changed_files
from stage4.static_checker import run_static_checks
from stage4.convention_sampler import get_convention_context
from stage4.prompt_builder import build_stage4_prompt, build_context_summary
from stage4.response_parser import parse_stage4_response


def run_stage4(repo_url: str, diff: str, bob_response: Optional[str] = None) -> dict:
    """
    Run Stage 4 pre-PR quality check pipeline
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
        diff: Unified git diff text
        bob_response: Optional Bob response to parse (if None, returns prompt only)
        
    Returns:
        Dictionary containing:
        - repo: Repository identifier
        - passes_check: Boolean (None if no bob_response)
        - summary: Summary of issues
        - issues: List of issues (empty if no bob_response)
        - prompt_for_bob: Prompt to copy to Bob IDE
        - metadata: Pipeline execution metadata
        
    Raises:
        Exception: If GitHub API fails or rate limit is hit
    """
    # Extract owner/repo from URL
    owner_repo = repo_url.replace("https://github.com/", "").strip("/")
    
    print(f"[Stage 4] Analyzing changes for repository: {owner_repo}")
    
    # Step 1: Parse diff
    print("[Stage 4] Parsing git diff...")
    parsed_diff = parse_diff(diff)
    
    changed_files = get_changed_files(parsed_diff)
    print(f"[Stage 4] Found {len(changed_files)} changed file(s)")
    
    if not changed_files:
        return {
            "repo": owner_repo,
            "passes_check": True,
            "summary": "No files changed",
            "issues": [],
            "prompt_for_bob": "",
            "metadata": {
                "files_changed": 0,
                "static_issues": 0,
                "convention_samples": 0
            }
        }
    
    # Step 2: Run static checks (deterministic, pre-Bob)
    print("[Stage 4] Running static analysis...")
    static_issues = run_static_checks(parsed_diff)
    print(f"[Stage 4] Found {len(static_issues)} static issue(s)")
    
    # Log static issues by severity
    static_by_severity = {"error": 0, "warning": 0, "info": 0}
    for issue in static_issues:
        severity = issue.get("severity", "info")
        static_by_severity[severity] = static_by_severity.get(severity, 0) + 1
    
    if static_issues:
        print(f"  - Errors: {static_by_severity['error']}")
        print(f"  - Warnings: {static_by_severity['warning']}")
        print(f"  - Info: {static_by_severity['info']}")
    
    # Step 3: Sample convention files (for Bob context)
    print("[Stage 4] Sampling repository conventions...")
    try:
        convention_context = get_convention_context(
            owner_repo,
            changed_files,
            samples_per_file=2
        )
        convention_count = sum(len(samples) for samples in convention_context.get("conventions", {}).values())
        print(f"[Stage 4] Sampled {convention_count} convention file(s)")
    except Exception as e:
        print(f"[Stage 4] Warning: Failed to sample conventions: {e}")
        convention_context = {
            "conventions": {},
            "summaries": {},
            "formatted": "Convention sampling failed."
        }
        convention_count = 0
    
    # Step 4: Build Bob prompt
    print("[Stage 4] Building prompt for Bob...")
    prompt = build_stage4_prompt(
        repo=owner_repo,
        parsed_diff=parsed_diff,
        convention_context=convention_context,
        static_issues=static_issues
    )
    
    context_summary = build_context_summary(parsed_diff, convention_context, static_issues)
    print(f"[Stage 4] Context: {context_summary}")
    
    # Step 5: Parse Bob response if provided
    if bob_response:
        print("[Stage 4] Parsing Bob response...")
        result = parse_stage4_response(bob_response, owner_repo, static_issues)
        
        print(f"[Stage 4] Final result: {result['summary']}")
        print(f"[Stage 4] Passes check: {result['passes_check']}")
        
        # Add prompt and metadata
        result["prompt_for_bob"] = prompt
        result["metadata"] = {
            "files_changed": len(changed_files),
            "static_issues": len(static_issues),
            "convention_samples": convention_count,
            "total_issues": len(result["issues"]),
            "static_errors": static_by_severity["error"],
            "static_warnings": static_by_severity["warning"],
            "static_info": static_by_severity["info"]
        }
        
        return result
    
    else:
        # No Bob response - return prompt only
        print("[Stage 4] No Bob response provided - returning prompt")
        
        return {
            "repo": owner_repo,
            "passes_check": None,
            "summary": f"Prompt ready - {len(static_issues)} static issues found",
            "issues": static_issues,  # Return static issues for preview
            "prompt_for_bob": prompt,
            "metadata": {
                "files_changed": len(changed_files),
                "static_issues": len(static_issues),
                "convention_samples": convention_count,
                "static_errors": static_by_severity["error"],
                "static_warnings": static_by_severity["warning"],
                "static_info": static_by_severity["info"]
            }
        }


# Made with Bob