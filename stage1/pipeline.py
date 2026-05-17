"""
Pipeline orchestrator for Stage 1 (Gap Finder)
Coordinates GitHub API fetching, data trimming, suspiciousness scoring, and prompt building
"""

from typing import Optional

from stage1.github_api import get_tree, get_commits, get_issues, get_file_content
from stage1.data_trimmer import (
    filter_source_files, trim_commits, trim_issues,
    trim_file_content, build_context_summary
)
from stage1.suspiciousness_scorer import score_and_rank_files
from stage1.prompt_builder import build_stage1_prompt, build_context_for_prompt
from stage1.response_parser import parse_stage1_response


def run_stage1(repo_url: str, bob_response: Optional[str] = None) -> dict:
    """
    Run Stage 1 gap finder pipeline
    
    Args:
        repo_url: GitHub repository URL (e.g., "https://github.com/owner/repo")
        bob_response: Optional Bob response to parse (if None, returns prompt only)
        
    Returns:
        Dictionary containing:
        - repo: Repository identifier
        - gaps: List of identified gaps (empty if bob_response is None)
        - prompt_for_bob: Prompt to copy to Bob IDE
        - metadata: Pipeline execution metadata
        
    Raises:
        Exception: If GitHub API fails or rate limit is hit
    """
    # Extract owner/repo from URL
    owner_repo = repo_url.replace("https://github.com/", "").strip("/")
    
    print(f"[Stage 1] Analyzing repository: {owner_repo}")
    
    # Step 1: Fetch GitHub data
    print("[Stage 1] Fetching repository tree...")
    tree = get_tree(owner_repo)
    
    print("[Stage 1] Fetching recent commits...")
    commits = get_commits(owner_repo, max_commits=50)
    
    print("[Stage 1] Fetching open issues...")
    issues = get_issues(owner_repo, max_issues=50)
    
    # Step 2: Trim data for token efficiency
    print("[Stage 1] Filtering source files...")
    source_files = filter_source_files(tree)
    
    print(f"[Stage 1] Found {len(source_files)} source files")
    
    trimmed_commits = trim_commits(commits, max_count=50)
    trimmed_issues = trim_issues(issues, max_count=50)
    
    # Build context summary
    context_summary = build_context_summary(source_files, trimmed_commits, trimmed_issues)
    
    # Step 3: Fetch file contents for scoring (limit to 100 files max)
    print("[Stage 1] Fetching file contents for analysis...")
    file_contents = {}
    files_to_analyze = source_files[:100]  # Limit to 100 files
    
    for i, file_info in enumerate(files_to_analyze):
        file_path = file_info.get("path", "")
        
        # Show progress every 20 files
        if (i + 1) % 20 == 0:
            print(f"[Stage 1] Fetched {i + 1}/{len(files_to_analyze)} files...")
        
        content = get_file_content(owner_repo, file_path)
        if content:
            # Trim content to 100 lines for scoring
            trimmed_content = trim_file_content(content, max_lines=100)
            file_contents[file_path] = trimmed_content
    
    print(f"[Stage 1] Successfully fetched {len(file_contents)} file contents")
    
    # Step 4: Score suspiciousness (pre-Bob optimization)
    print("[Stage 1] Scoring file suspiciousness...")
    top_suspicious = score_and_rank_files(
        source_files=files_to_analyze,
        file_contents=file_contents,
        commits=trimmed_commits,
        top_k=5
    )
    
    print(f"[Stage 1] Identified top {len(top_suspicious)} suspicious files")
    
    # Log suspicious files
    for i, (score, file_path, _, reasons) in enumerate(top_suspicious, 1):
        print(f"  {i}. {file_path} (score: {score:.2f})")
        for reason in reasons:
            print(f"     - {reason}")
    
    # Step 5: Build Bob prompt
    print("[Stage 1] Building prompt for Bob...")
    context = build_context_for_prompt(
        commits=trimmed_commits,
        issues=trimmed_issues,
        summary=context_summary
    )
    
    prompt = build_stage1_prompt(
        repo=owner_repo,
        suspicious_files=top_suspicious,
        context=context
    )
    
    # Step 6: Parse Agent response (automated)
    gaps = []
    if not bob_response:
        print("[Stage 1] Invoking AI Agent to analyze gaps...")
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            bob_response = llm.invoke(prompt).content
        except Exception as e:
            print(f"[Stage 1] Warning: LLM call failed: {e}")

    if bob_response:
        print("[Stage 1] Parsing Agent response...")
        parsed = parse_stage1_response(bob_response, owner_repo)
        gaps = parsed.get("gaps", [])
        print(f"[Stage 1] Identified {len(gaps)} gaps")
    
    # Build metadata
    metadata = {
        "total_files": len(source_files),
        "files_analyzed": len(file_contents),
        "suspicious_files": len(top_suspicious),
        "commits_analyzed": len(trimmed_commits),
        "issues_analyzed": len(trimmed_issues)
    }
    
    # Return result
    result = {
        "repo": owner_repo,
        "gaps": gaps,
        "prompt_for_bob": prompt,
        "metadata": metadata
    }
    
    print("[Stage 1] Pipeline complete!")
    
    return result


# Made with Bob