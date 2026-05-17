"""
Pipeline orchestrator for Stage 2 (Idea Deduplication)
Coordinates GitHub API fetching, semantic matching, and prompt building
"""

from stage2.github_api import get_issues, get_pull_requests
from stage2.semantic_matcher import get_top_matches
from stage2.prompt_builder import build_stage2_prompt, assemble_stage2_context


def _build_recommendation(status: str, conflicts: list, idea: str) -> tuple[str, str]:
    """Build recommendation code and human-readable text per IO Design spec"""
    if status == "conflict":
        first = conflicts[0] if conflicts else {}
        num = first.get("number", "")
        type_ = first.get("type", "issue")
        return (
            "conflict_found",
            f"This idea is already being worked on. Consider commenting on {type_.upper()} #{num} "
            f"to collaborate rather than opening a duplicate."
        )
    elif status == "complementary":
        return (
            "partial_overlap",
            "Related work exists but your idea adds distinct value. Consider referencing existing work in your PR description."
        )
    else:
        return (
            "proceed",
            "Safe to proceed. No existing issues or PRs cover this idea. You're clear to open a new issue or PR."
        )


def run_stage2(repo_url: str, idea: str) -> dict:
    """
    Run Stage 2 idea deduplication pipeline with direct conflict analysis
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
        idea: Contribution idea in plain English
        
    Returns:
        Dictionary containing:
        - repo: Repository identifier
        - idea: Original contribution idea
        - status: "conflict", "complementary", or "clear"
        - conflicts: List of conflicting issues/PRs with summaries
        
    Raises:
        Exception: If GitHub API fails or rate limit is hit
    """
    # Extract owner/repo from URL
    owner_repo = repo_url.replace("https://github.com/", "").strip("/")
    
    # Fetch issues and PRs from GitHub
    issues = get_issues(owner_repo, max_issues=50)
    prs = get_pull_requests(owner_repo, max_prs=50)
    
    # Find semantic matches using embeddings
    top_matches = get_top_matches(
        idea=idea,
        issues=issues,
        prs=prs,
        top_k=5,
        threshold=0.5
    )
    
    # Build context summary and prompt
    context = assemble_stage2_context(issues, prs, top_k=5)
    prompt = build_stage2_prompt(owner_repo, idea, top_matches)
    
    # Analyze conflicts and determine status
    conflicts = []
    status = "clear"
    has_complementary = False
    
    for match in top_matches:
        similarity = match["similarity"]
        match_type = match["type"]
        state = match["state"]
        merged = match.get("merged", False)
        
        # Determine if this is a real conflict
        is_conflict = False
        summary = ""
        
        if similarity >= 0.7:
            # High similarity - likely conflict
            if state == "open":
                is_conflict = True
                summary = f"This {match_type} is currently open and directly addresses the same functionality."
            elif match_type == "pr" and merged:
                is_conflict = True
                summary = f"This PR was already merged, implementing similar functionality."
            elif state == "closed" and match_type == "issue":
                # Check if it was rejected or completed
                labels = match.get("labels", [])
                if any(label in ["wontfix", "rejected", "invalid"] for label in labels):
                    summary = f"This issue was closed as '{labels[0]}' - your idea may still be viable."
                else:
                    is_conflict = True
                    summary = f"This issue was closed, possibly already resolved."
        elif similarity >= 0.5:
            # Medium similarity - complementary or related
            if state == "open":
                summary = f"This {match_type} is related but focuses on a different aspect."
                has_complementary = True
        
        if is_conflict:
            status = "conflict"
            conflicts.append({
                "type": match_type,
                "number": match["number"],
                "url": match["url"],
                "title": match["title"],
                "state": state,
                "assigned": bool(match.get("assignee")),
                "assignee": match.get("assignee", None),
                "similarity": round(similarity, 2),
                "summary": summary,
                "recommendation": "comment" if state == "open" else "reference"
            })

    # Set status based on findings
    if status != "conflict" and has_complementary:
        status = "complementary"

    recommendation, recommendation_text = _build_recommendation(status, conflicts, idea)

    # Return structured response — fully compliant with ContribFlow_IO_Design.md
    return {
        "repo": owner_repo,
        "idea": idea,
        "status": status,
        "checked_against": {
            "open_issues": sum(1 for i in issues if i.get("state") == "open"),
            "closed_issues": sum(1 for i in issues if i.get("state") == "closed"),
            "open_prs": sum(1 for p in prs if p.get("state") == "open"),
            "closed_prs": sum(1 for p in prs if p.get("state") == "closed"),
        },
        "conflicts": conflicts,
        "recommendation": recommendation,
        "recommendation_text": recommendation_text,
        "prompt_for_bob": prompt
    }

# Made with Bob
