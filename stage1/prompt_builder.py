"""
Prompt builder for Stage 1 (Gap Finder)
Assembles context and builds Bob-ready prompts for gap identification
"""

from typing import List, Dict, Tuple


def build_stage1_prompt(
    repo: str,
    suspicious_files: List[Tuple[float, str, str, List[str]]],
    context: Dict
) -> str:
    """
    Build Bob prompt for gap identification reasoning
    
    Args:
        repo: Repository in format "owner/repo"
        suspicious_files: List of (score, path, content, reasons) tuples
        context: Dictionary with repository context (commits, issues, summary)
        
    Returns:
        Formatted prompt string for Bob
    """
    
    # Build suspicious files section
    files_section = "\n\nTop Suspicious Files (pre-scored by heuristics):\n"
    
    for i, (score, file_path, content, reasons) in enumerate(suspicious_files, 1):
        files_section += f"\n{i}. {file_path} (suspiciousness score: {score:.2f})\n"
        files_section += f"   Reasons:\n"
        for reason in reasons:
            files_section += f"   - {reason}\n"
    
    # Build context section
    context_summary = context.get("summary", {})
    commits = context.get("commits", [])
    issues = context.get("issues", [])
    
    context_section = f"""
Repository Context:
- Total source files: {context_summary.get('total_files', 0)}
- File types: {', '.join(f"{ext}({count})" for ext, count in list(context_summary.get('file_types', {}).items())[:5])}
- Recent commits: {len(commits)}
- Open issues: {len(issues)}
"""
    
    # Add most active files if available
    most_active = context_summary.get("most_active_files", [])
    if most_active:
        context_section += "\nMost active files (recent commits):\n"
        for file_info in most_active[:5]:
            context_section += f"- {file_info['path']} ({file_info['changes']} changes)\n"
    
    # Add recent issues if available
    if issues:
        context_section += f"\nRecent open issues (top {min(5, len(issues))}):\n"
        for issue in issues[:5]:
            context_section += f"- #{issue['number']}: {issue['title']}\n"
    
    # Build file contents section
    contents_section = "\n\nFile Contents (first 100 lines each):\n"
    
    for i, (score, file_path, content, reasons) in enumerate(suspicious_files, 1):
        lines = content.split("\n")
        trimmed_content = "\n".join(lines[:100])
        
        if len(lines) > 100:
            trimmed_content += f"\n... (truncated, {len(lines) - 100} more lines)"
        
        contents_section += f"\n{'='*60}\n"
        contents_section += f"File {i}: {file_path}\n"
        contents_section += f"{'='*60}\n"
        contents_section += trimmed_content + "\n"
    
    # Build the complete prompt
    prompt = f"""You are analyzing a GitHub repository to identify meaningful contribution gaps.

Repository: {repo}
{files_section}
{context_section}
{contents_section}

Your task:
Identify 3-5 meaningful contribution gaps that would make valuable contributions to this repository.

Focus on:
✅ Missing error handling in risky operations
✅ Missing test coverage for critical functions
✅ TODO/FIXME items that need implementation
✅ Deprecated dependencies that should be updated
✅ Unimplemented functionality (pass statements, NotImplementedError)
✅ Core modules with suspicious patterns

DO NOT report:
❌ Typos or spelling mistakes
❌ README or documentation formatting
❌ Code style or formatting issues
❌ Minor refactoring suggestions

Requirements:
1. Ground your reasoning in ACTUAL CODE from the files above
2. Quote specific line numbers or code snippets as evidence
3. Prioritize high-impact gaps in core modules
4. Explain WHY each gap matters (not just WHAT is missing)
5. Consider the repository context (recent activity, open issues)

Return ONLY valid JSON matching this exact schema:
{{
  "repo": "{repo}",
  "gaps": [
    {{
      "title": "One-line description of the gap",
      "file": "path/to/file.py",
      "impact": "high|medium|low",
      "category": "error-handling|test-coverage|todo-fixme|deprecated-deps|unimplemented",
      "reasoning": "2-3 sentences explaining the gap with specific code evidence. Quote actual code or line numbers."
    }}
  ]
}}

Impact levels:
- high: Affects core functionality, could cause crashes or data loss
- medium: Affects secondary features, could cause bugs
- low: Nice-to-have improvements, minor issues

Categories:
- error-handling: Missing try/except, no validation, unhandled edge cases
- test-coverage: Missing tests for critical functions
- todo-fixme: TODO/FIXME comments indicating incomplete work
- deprecated-deps: Using deprecated libraries or APIs
- unimplemented: Functions with pass statements or NotImplementedError

Provide the JSON output now. No markdown formatting, just raw JSON."""

    return prompt


def build_context_for_prompt(
    commits: List[Dict],
    issues: List[Dict],
    summary: Dict
) -> Dict:
    """
    Build context dictionary for prompt builder
    
    Args:
        commits: List of trimmed commits
        issues: List of trimmed issues
        summary: Repository summary from data_trimmer
        
    Returns:
        Context dictionary
    """
    return {
        "commits": commits,
        "issues": issues,
        "summary": summary
    }


# Made with Bob