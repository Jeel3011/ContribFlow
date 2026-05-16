"""
Prompt builder for Stage 2 (Idea Deduplication)
Assembles context and builds Bob-ready prompts for semantic conflict reasoning
"""

from typing import List, Dict


def build_stage2_prompt(repo: str, idea: str, top_matches: List[Dict]) -> str:
    """
    Build Bob prompt for idea deduplication reasoning
    
    Args:
        repo: Repository in format "owner/repo"
        idea: Contribution idea text
        top_matches: List of top semantic matches with similarity scores
        
    Returns:
        Formatted prompt string for Bob
    """
    # Build matches section
    matches_section = ""
    if top_matches:
        matches_section = "\n\nTop semantic matches found:\n"
        for i, match in enumerate(top_matches, 1):
            match_type = match["type"].upper()
            state = match["state"]
            merged_info = f" (merged)" if match.get("merged") else ""
            similarity = match["similarity"]
            
            matches_section += f"\n{i}. [{match_type} #{match['number']}] {match['title']}\n"
            matches_section += f"   State: {state}{merged_info}\n"
            matches_section += f"   Similarity: {similarity:.2f}\n"
            matches_section += f"   URL: {match['url']}\n"
    else:
        matches_section = "\n\nNo semantic matches found above threshold."
    
    prompt = f"""You are analyzing whether a contribution idea conflicts with existing work in a GitHub repository.

Repository: {repo}
Contribution Idea: {idea}
{matches_section}

Your task:
1. Analyze if the contribution idea conflicts with any existing issues or PRs
2. Consider semantic meaning, not just keywords
3. Distinguish between:
   - CONFLICT: Idea duplicates existing work or would conflict with merged/open work
   - COMPLEMENTARY: Idea builds on or extends existing work without conflict
   - CLEAR: No conflicts found

Rules for conflict detection:
- Open issues/PRs with high similarity (≥0.7) are likely conflicts
- Closed/merged PRs with high similarity may indicate the work is already done
- Closed issues marked as "wontfix" or "rejected" are NOT conflicts (idea can proceed)
- Low similarity (<0.5) generally indicates no conflict
- Consider the state: open vs closed, merged vs rejected

Return ONLY valid JSON, no markdown:
{{
  "repo": "{repo}",
  "idea": "{idea[:100]}...",
  "status": "conflict|complementary|clear",
  "conflicts": [
    {{
      "type": "issue|pr",
      "number": 0,
      "url": "",
      "title": "",
      "similarity": 0.0,
      "summary": "Brief explanation of why this is a conflict"
    }}
  ],
  "reasoning": "Your analysis of why conflicts exist or don't exist",
  "recommendation": "proceed|revise|abandon"
}}

If status is "clear", conflicts array should be empty.
If status is "complementary", explain how the idea relates to existing work.
If status is "conflict", list all conflicting items with explanations."""

    return prompt


def assemble_stage2_context(issues: List[Dict], prs: List[Dict], top_k: int = 5) -> str:
    """
    Assemble context summary of repository issues/PRs for reference
    
    Args:
        issues: List of issue dictionaries
        prs: List of PR dictionaries
        top_k: Number of recent items to include
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    context_parts.append(f"Repository has {len(issues)} issues and {len(prs)} PRs")
    
    if issues:
        context_parts.append(f"\nRecent issues (top {min(top_k, len(issues))}):")
        for issue in issues[:top_k]:
            state = issue["state"]
            context_parts.append(f"  - #{issue['number']}: {issue['title']} [{state}]")
    
    if prs:
        context_parts.append(f"\nRecent PRs (top {min(top_k, len(prs))}):")
        for pr in prs[:top_k]:
            state = pr["state"]
            merged = " (merged)" if pr.get("merged") else ""
            context_parts.append(f"  - #{pr['number']}: {pr['title']} [{state}{merged}]")
    
    return "\n".join(context_parts)

# Made with Bob
