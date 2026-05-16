"""
Prompt Builder for Stage 4 (Pre-PR Quality Check)
Generates Bob prompts for AI-powered code review
"""

from typing import Dict, List


def build_stage4_prompt(
    repo: str,
    parsed_diff: Dict,
    convention_context: Dict,
    static_issues: List[Dict]
) -> str:
    """
    Build comprehensive Bob prompt for code review
    
    Args:
        repo: Repository identifier (owner/repo)
        parsed_diff: Output from diff_parser.parse_diff()
        convention_context: Output from convention_sampler.get_convention_context()
        static_issues: Output from static_checker.run_static_checks()
        
    Returns:
        Formatted prompt string for Bob
    """
    prompt_parts = []
    
    # Header
    prompt_parts.append("# Stage 4: Pre-PR Quality Check")
    prompt_parts.append(f"\nRepository: `{repo}`\n")
    
    # Task description
    prompt_parts.append("## Task")
    prompt_parts.append("""
You are a senior software engineer performing a pre-PR code review.
Analyze the provided git diff and identify code quality issues that should be addressed before submitting a pull request.

Focus on:
- Code style and conventions (based on repository patterns)
- Potential bugs or logic errors
- Performance concerns
- Security vulnerabilities
- Missing error handling
- Incomplete implementations
- Breaking changes

Do NOT report:
- Issues already caught by static analysis (listed below)
- Trivial formatting issues
- Personal style preferences
""")
    
    # Diff summary
    prompt_parts.append("\n## Changes Summary")
    prompt_parts.append(format_diff_summary(parsed_diff))
    
    # Detailed diff
    prompt_parts.append("\n## Detailed Diff")
    prompt_parts.append(format_diff_for_prompt(parsed_diff))
    
    # Convention context
    if convention_context.get("formatted"):
        prompt_parts.append("\n## Repository Conventions")
        prompt_parts.append(convention_context["formatted"])
    
    # Static issues already found
    if static_issues:
        prompt_parts.append("\n## Static Analysis Results")
        prompt_parts.append("The following issues were already detected by static analysis (do NOT repeat these):\n")
        for issue in static_issues[:10]:  # Limit to 10 to save tokens
            prompt_parts.append(f"- {issue['severity'].upper()}: {issue['file']}:{issue['line']} - {issue['issue']}")
    
    # Output format instructions
    prompt_parts.append("\n## Required Output Format")
    prompt_parts.append("""
Respond with a JSON object in this EXACT format:

```json
{
  "issues": [
    {
      "severity": "error",
      "file": "src/app.py",
      "line": "42",
      "issue": "Brief description of the issue",
      "fix": "Suggested fix or improvement"
    }
  ]
}
```

Severity levels:
- "error": Critical issues that will cause bugs or failures
- "warning": Potential problems or bad practices
- "info": Suggestions for improvement

Rules:
- Only include issues requiring human judgment (not static analysis)
- Be specific about file paths and line numbers
- Provide actionable fix suggestions
- Maximum 10 issues (prioritize most important)
- If no issues found, return empty issues array: {"issues": []}
""")
    
    return "\n".join(prompt_parts)


def format_diff_summary(parsed_diff: Dict) -> str:
    """
    Format diff statistics into summary
    
    Args:
        parsed_diff: Output from diff_parser.parse_diff()
        
    Returns:
        Formatted summary string
    """
    stats = parsed_diff["stats"]
    files = parsed_diff["files"]
    
    lines = []
    lines.append(f"**Files changed:** {stats['files_changed']}")
    lines.append(f"**Additions:** +{stats['additions']}")
    lines.append(f"**Deletions:** -{stats['deletions']}")
    lines.append("\n**Modified files:**")
    
    for file in files:
        status_emoji = {
            "added": "✨",
            "deleted": "🗑️",
            "modified": "📝",
            "renamed": "📛"
        }.get(file["status"], "📄")
        
        lines.append(f"- {status_emoji} `{file['path']}` ({file['language']}) +{len(file['additions'])} -{len(file['deletions'])}")
    
    return "\n".join(lines)


def format_diff_for_prompt(parsed_diff: Dict) -> str:
    """
    Format detailed diff for Bob prompt
    
    Args:
        parsed_diff: Output from diff_parser.parse_diff()
        
    Returns:
        Formatted diff string
    """
    lines = []
    
    for file in parsed_diff["files"]:
        lines.append(f"\n### {file['path']} ({file['status']})")
        lines.append(f"Language: {file['language']}")
        lines.append("")
        
        # Show chunks with context
        for chunk in file["chunks"]:
            lines.append(f"```diff")
            lines.append(f"@@ -{chunk['old_start']},{chunk['old_count']} +{chunk['new_start']},{chunk['new_count']} @@")
            
            for line_info in chunk["lines"]:
                if line_info["type"] == "addition":
                    lines.append(f"+{line_info['content']}")
                elif line_info["type"] == "deletion":
                    lines.append(f"-{line_info['content']}")
                else:  # context
                    lines.append(f" {line_info['content']}")
            
            lines.append("```")
            lines.append("")
    
    return "\n".join(lines)


def format_static_issues_summary(static_issues: List[Dict]) -> str:
    """
    Format static issues into readable summary
    
    Args:
        static_issues: List of issues from static_checker
        
    Returns:
        Formatted summary string
    """
    if not static_issues:
        return "No static analysis issues found."
    
    # Group by severity
    by_severity = {"error": [], "warning": [], "info": []}
    for issue in static_issues:
        severity = issue.get("severity", "info")
        by_severity[severity].append(issue)
    
    lines = []
    lines.append(f"**Total issues:** {len(static_issues)}")
    lines.append(f"- Errors: {len(by_severity['error'])}")
    lines.append(f"- Warnings: {len(by_severity['warning'])}")
    lines.append(f"- Info: {len(by_severity['info'])}")
    
    return "\n".join(lines)


def build_context_summary(
    parsed_diff: Dict,
    convention_context: Dict,
    static_issues: List[Dict]
) -> str:
    """
    Build high-level context summary for logging/display
    
    Args:
        parsed_diff: Parsed diff
        convention_context: Convention context
        static_issues: Static issues
        
    Returns:
        Summary string
    """
    stats = parsed_diff["stats"]
    
    lines = []
    lines.append(f"Files changed: {stats['files_changed']}")
    lines.append(f"Lines: +{stats['additions']} -{stats['deletions']}")
    lines.append(f"Static issues: {len(static_issues)}")
    
    convention_count = sum(len(samples) for samples in convention_context.get("conventions", {}).values())
    lines.append(f"Convention samples: {convention_count}")
    
    return " | ".join(lines)


# Made with Bob