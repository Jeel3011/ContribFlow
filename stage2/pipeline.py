"""
Pipeline orchestrator for Stage 2 (Idea Deduplication)
Coordinates GitHub API fetching, semantic matching, and prompt building
"""

from stage2.github_api import get_issues, get_pull_requests
from stage2.semantic_matcher import get_top_matches
from stage2.prompt_builder import build_stage2_prompt, assemble_stage2_context
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ConflictVerdict(BaseModel):
    number: int = Field(description="The issue or PR number")
    verdict: str = Field(description="'conflict', 'complementary', or 'unrelated'")
    summary: str = Field(description="1-2 sentences explaining why it is a conflict or complementary")

class Stage2LLMResponse(BaseModel):
    verdicts: list[ConflictVerdict]

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
    
    if top_matches:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(Stage2LLMResponse)
        
        candidates_json = json.dumps([
            {"number": m["number"], "type": m["type"], "title": m["title"], "state": m["state"], "url": m["url"], "similarity": m["similarity"], "merged": m.get("merged", False)}
            for m in top_matches
        ], indent=2)
        
        prompt_text = f"""Given this contribution idea: "{idea}"
        
And these existing issues/PRs from {owner_repo}:
{candidates_json}

For each candidate, classify as:
- "conflict": Directly overlaps, doing this would be duplicate work (especially if open or recently merged)
- "complementary": Related but adds distinct value
- "unrelated": False positive, not actually related

Provide a summary explaining why.
"""
        try:
            llm_result = llm.invoke([HumanMessage(content=prompt_text)])
            verdict_map = {v.number: v for v in llm_result.verdicts}
            
            for match in top_matches:
                v = verdict_map.get(match["number"])
                if not v:
                    continue
                    
                if v.verdict == "conflict":
                    status = "conflict"
                    conflicts.append({
                        "type": match["type"],
                        "number": match["number"],
                        "url": match["url"],
                        "title": match["title"],
                        "state": match["state"],
                        "assigned": bool(match.get("assignee")),
                        "assignee": match.get("assignee", None),
                        "similarity": round(match["similarity"], 2),
                        "summary": v.summary,
                        "recommendation": "comment" if match["state"] == "open" else "reference"
                    })
                elif v.verdict == "complementary":
                    has_complementary = True
                    # Optional: Include complementary in conflicts list? Spec says 'conflicts' array. 
                    # We'll just set the flag to upgrade status to complementary if no conflicts.
        except Exception as e:
            logger.error(f"LLM verification failed: {e}")
            # Fallback to simple threshold if LLM fails
            for match in top_matches:
                if match["similarity"] >= 0.7:
                    status = "conflict"
                    conflicts.append({
                        "type": match["type"],
                        "number": match["number"],
                        "url": match["url"],
                        "title": match["title"],
                        "state": match["state"],
                        "assigned": bool(match.get("assignee")),
                        "assignee": match.get("assignee", None),
                        "similarity": round(match["similarity"], 2),
                        "summary": "Likely conflict based on semantic similarity.",
                        "recommendation": "comment"
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
