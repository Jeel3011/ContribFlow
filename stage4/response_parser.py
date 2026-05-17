"""
Response Parser for Stage 4 (Pre-PR Quality Check)
Parses Bob's JSON responses and merges with static analysis results
"""

import json
import re
from typing import Dict, List, Optional


def extract_json_from_response(raw_response: str) -> Optional[str]:
    """
    Extract JSON from Bob's response (may be wrapped in markdown)
    
    Args:
        raw_response: Raw response from Bob
        
    Returns:
        Extracted JSON string, or None if not found
    """
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find raw JSON object
    json_match = re.search(r'\{.*"issues".*\}', raw_response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return None


def parse_stage4_response(raw_response: str, repo: str, static_issues: List[Dict]) -> Dict:
    """
    Parse Bob response and merge with static analysis results
    
    Args:
        raw_response: Raw response from Bob
        repo: Repository identifier (owner/repo)
        static_issues: Issues from static analysis
        
    Returns:
        Structured response:
        {
            "repo": "owner/repo",
            "passes_check": false,
            "summary": "3 errors, 2 warnings, 1 info",
            "issues": [...]
        }
    """
    # Extract JSON from response
    json_str = extract_json_from_response(raw_response)
    
    bob_issues = []
    if json_str:
        try:
            data = json.loads(json_str)
            bob_issues = data.get("issues", [])

            # Add source + category attribution
            for issue in bob_issues:
                issue["source"] = issue.get("source", "bob")
                if not issue.get("category"):
                    # Infer category from issue text
                    text = issue.get("issue", "").lower()
                    if "convention" in text or "annotation" in text or "docstring" in text:
                        issue["category"] = "convention-violation"
                    elif "pattern" in text or "inconsistent" in text:
                        issue["category"] = "pattern-inconsistency"
                    elif "test" in text:
                        issue["category"] = "missing-test"
                    elif "unused" in text or "import" in text:
                        issue["category"] = "cleanup"
                    else:
                        issue["category"] = "logic-bug"

        except json.JSONDecodeError as e:
            print(f"[Stage 4] Warning: Failed to parse Bob response JSON: {e}")

    # Merge static and Bob issues
    all_issues = merge_static_and_ai_issues(static_issues, bob_issues)
    all_issues = sort_issues_by_severity(all_issues)

    # Add IDs and ensure category on static issues
    for i, issue in enumerate(all_issues, 1):
        if "id" not in issue:
            issue["id"] = f"i{i:03d}"
        if not issue.get("category"):
            issue["category"] = "cleanup"

    # Generate summary and pass/fail
    summary = generate_summary(all_issues)
    passes_check = not any(issue["severity"] == "error" for issue in all_issues)

    return {
        "repo": repo,
        "passes_check": passes_check,
        "summary": summary,
        "issues": all_issues
    }


def merge_static_and_ai_issues(static_issues: List[Dict], ai_issues: List[Dict]) -> List[Dict]:
    """
    Merge static and AI issues, removing duplicates.

    Args:
        static_issues: Issues from static analysis
        ai_issues: Issues from Bob

    Returns:
        Merged list of issues
    """
    from stage4.static_checker import safe_line_number

    merged = list(static_issues)

    for ai_issue in ai_issues:
        is_duplicate = False

        for static_issue in static_issues:
            if (ai_issue.get("file") == static_issue.get("file") and
                    abs(safe_line_number(ai_issue.get("line", "0")) -
                        safe_line_number(static_issue.get("line", "0"))) <= 2):
                if similar_text(ai_issue.get("issue", ""), static_issue.get("issue", "")):
                    is_duplicate = True
                    break

        if not is_duplicate:
            merged.append(ai_issue)

    return merged


def similar_text(text1: str, text2: str, threshold: float = 0.5) -> bool:
    """
    Check if two text strings are similar (simple word overlap)
    
    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold (0.0-1.0)
        
    Returns:
        True if texts are similar
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return False
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    similarity = len(intersection) / len(union)
    return similarity >= threshold


def sort_issues_by_severity(issues: List[Dict]) -> List[Dict]:
    """
    Sort issues by severity (error > warning > info)
    
    Args:
        issues: List of issues
        
    Returns:
        Sorted list
    """
    severity_order = {"error": 0, "warning": 1, "info": 2}
    
    return sorted(issues, key=lambda x: severity_order.get(x.get("severity", "info"), 3))


def generate_summary(issues: List[Dict]) -> str:
    """
    Generate human-readable summary of issues
    
    Args:
        issues: List of issues
        
    Returns:
        Summary string (e.g., "3 errors, 2 warnings, 1 info")
    """
    if not issues:
        return "No issues found"
    
    # Count by severity
    counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity = issue.get("severity", "info")
        counts[severity] = counts.get(severity, 0) + 1
    
    # Build summary
    parts = []
    if counts["error"] > 0:
        parts.append(f"{counts['error']} error{'s' if counts['error'] != 1 else ''}")
    if counts["warning"] > 0:
        parts.append(f"{counts['warning']} warning{'s' if counts['warning'] != 1 else ''}")
    if counts["info"] > 0:
        parts.append(f"{counts['info']} info")
    
    return ", ".join(parts)


def validate_issue(issue: Dict) -> bool:
    """
    Validate that an issue has required fields
    
    Args:
        issue: Issue dictionary
        
    Returns:
        True if valid
    """
    required_fields = ["severity", "file", "line", "issue", "fix"]
    
    for field in required_fields:
        if field not in issue or not issue[field]:
            return False
    
    # Validate severity
    if issue["severity"] not in ["error", "warning", "info"]:
        return False
    
    return True


def format_issues_for_display(issues: List[Dict]) -> str:
    """
    Format issues for human-readable display
    
    Args:
        issues: List of issues
        
    Returns:
        Formatted string
    """
    if not issues:
        return "✅ No issues found!"
    
    lines = []
    
    # Group by severity
    by_severity = {"error": [], "warning": [], "info": []}
    for issue in issues:
        severity = issue.get("severity", "info")
        by_severity[severity].append(issue)
    
    # Format errors
    if by_severity["error"]:
        lines.append(f"\n❌ ERRORS ({len(by_severity['error'])})")
        for issue in by_severity["error"]:
            lines.append(f"  {issue['file']}:{issue['line']}")
            lines.append(f"    Issue: {issue['issue']}")
            lines.append(f"    Fix: {issue['fix']}")
            lines.append(f"    Source: {issue.get('source', 'unknown')}")
            lines.append("")
    
    # Format warnings
    if by_severity["warning"]:
        lines.append(f"\n⚠️  WARNINGS ({len(by_severity['warning'])})")
        for issue in by_severity["warning"]:
            lines.append(f"  {issue['file']}:{issue['line']}")
            lines.append(f"    Issue: {issue['issue']}")
            lines.append(f"    Fix: {issue['fix']}")
            lines.append(f"    Source: {issue.get('source', 'unknown')}")
            lines.append("")
    
    # Format info
    if by_severity["info"]:
        lines.append(f"\nℹ️  INFO ({len(by_severity['info'])})")
        for issue in by_severity["info"]:
            lines.append(f"  {issue['file']}:{issue['line']}")
            lines.append(f"    Issue: {issue['issue']}")
            lines.append(f"    Fix: {issue['fix']}")
            lines.append(f"    Source: {issue.get('source', 'unknown')}")
            lines.append("")
    
    return "\n".join(lines)


# Made with Bob