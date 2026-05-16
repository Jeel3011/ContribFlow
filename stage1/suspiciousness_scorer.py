"""
Suspiciousness scoring heuristic for Stage 1 (Gap Finder)
Pre-selects top suspicious files BEFORE Bob to save tokens (AGENTS.md requirement)
"""

import re
from typing import List, Dict, Tuple


def score_file_suspiciousness(
    file_path: str,
    content: str,
    commits: List[Dict]
) -> float:
    """
    Score file suspiciousness based on multiple heuristics
    
    Args:
        file_path: Path to the file
        content: File content
        commits: List of recent commits
        
    Returns:
        Suspiciousness score (0.0-1.0), higher = more likely to have gaps
        
    Scoring factors:
        - TODO/FIXME comments (+0.3 max)
        - Missing error handling (+0.25)
        - Deprecated imports (+0.2)
        - Unimplemented functions (+0.15)
        - Core module weighting (+0.1)
        - Recent activity (+0.1)
    """
    score = 0.0
    content_lower = content.lower()
    
    # 1. TODO/FIXME detection (+0.3 max)
    todo_count = content_lower.count("todo")
    fixme_count = content_lower.count("fixme")
    hack_count = content_lower.count("hack")
    xxx_count = content_lower.count("xxx")
    
    total_markers = todo_count + fixme_count + hack_count + xxx_count
    score += min(total_markers * 0.1, 0.3)
    
    # 2. Missing error handling (+0.25)
    # Check for risky operations without try/except
    has_try = "try:" in content_lower or "try {" in content_lower
    
    risky_patterns = [
        r'open\s*\(',           # File operations
        r'requests\.',          # HTTP requests
        r'json\.loads',         # JSON parsing
        r'json\.parse',         # JSON parsing (JS)
        r'fetch\(',             # Fetch API
        r'axios\.',             # Axios
        r'\.read\(',            # File reading
        r'\.write\(',           # File writing
        r'subprocess\.',        # Subprocess calls
        r'exec\(',              # Code execution
        r'eval\('               # Code evaluation
    ]
    
    risky_operations = sum(1 for pattern in risky_patterns if re.search(pattern, content, re.IGNORECASE))
    
    if risky_operations > 0 and not has_try:
        score += min(risky_operations * 0.08, 0.25)
    
    # 3. Deprecated imports (+0.2)
    deprecated_patterns = {
        "python": ["optparse", "imp", "md5", "sha", "sets", "string.atoi"],
        "javascript": ["request", "node-uuid"],
        "general": []
    }
    
    all_deprecated = deprecated_patterns["python"] + deprecated_patterns["javascript"]
    deprecated_found = sum(1 for dep in all_deprecated if f"import {dep}" in content_lower or f"require('{dep}')" in content_lower)
    
    if deprecated_found > 0:
        score += min(deprecated_found * 0.1, 0.2)
    
    # 4. Unimplemented functions (+0.15)
    unimplemented_patterns = [
        r'^\s*pass\s*$',                    # Python pass statement
        r'raise\s+NotImplementedError',     # NotImplementedError
        r'throw\s+new\s+Error\(["\']Not implemented',  # JS not implemented
        r'TODO:\s*implement',               # TODO implement comments
        r'function\s+\w+\s*\([^)]*\)\s*\{\s*\}',  # Empty functions
    ]
    
    unimplemented_count = sum(1 for pattern in unimplemented_patterns if re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
    
    if unimplemented_count > 0:
        score += min(unimplemented_count * 0.05, 0.15)
    
    # 5. Core module weighting (+0.1)
    # Files in core directories or with core names are more important
    core_indicators = [
        "main", "core", "app", "server", "api", "pipeline",
        "service", "controller", "handler", "manager", "engine"
    ]
    
    path_lower = file_path.lower()
    if any(indicator in path_lower for indicator in core_indicators):
        score += 0.1
    
    # 6. Recent activity (+0.1)
    # Files with many recent changes might have gaps
    recent_changes = sum(1 for commit in commits if file_path in commit.get("files", []))
    
    if recent_changes >= 5:
        score += 0.1
    elif recent_changes >= 3:
        score += 0.05
    
    # 7. Missing documentation (+0.05)
    # Check for docstrings/comments
    has_docstring = '"""' in content or "'''" in content or "/**" in content
    comment_ratio = (content.count("#") + content.count("//")) / max(content.count("\n"), 1)
    
    if not has_docstring and comment_ratio < 0.05:
        score += 0.05
    
    # 8. Large functions without error handling (+0.1)
    # Detect large function blocks
    function_patterns = [
        r'def\s+\w+\s*\([^)]*\):',  # Python functions
        r'function\s+\w+\s*\([^)]*\)\s*\{',  # JS functions
        r'const\s+\w+\s*=\s*\([^)]*\)\s*=>'  # Arrow functions
    ]
    
    lines = content.split("\n")
    large_functions = 0
    
    for i, line in enumerate(lines):
        if any(re.search(pattern, line) for pattern in function_patterns):
            # Count lines until next function or end
            func_lines = 0
            for j in range(i + 1, min(i + 100, len(lines))):
                if any(re.search(pattern, lines[j]) for pattern in function_patterns):
                    break
                func_lines += 1
            
            if func_lines > 50 and not has_try:
                large_functions += 1
    
    if large_functions > 0:
        score += min(large_functions * 0.05, 0.1)
    
    return min(score, 1.0)


def get_suspiciousness_reasons(
    file_path: str,
    content: str,
    commits: List[Dict]
) -> List[str]:
    """
    Get human-readable reasons for suspiciousness score
    
    Args:
        file_path: Path to the file
        content: File content
        commits: List of recent commits
        
    Returns:
        List of reason strings
    """
    reasons = []
    content_lower = content.lower()
    
    # TODO/FIXME markers
    todo_count = content_lower.count("todo") + content_lower.count("fixme")
    if todo_count > 0:
        reasons.append(f"{todo_count} TODO/FIXME comment(s) found")
    
    # Missing error handling
    has_try = "try:" in content_lower or "try {" in content_lower
    risky_patterns = [r'open\s*\(', r'requests\.', r'json\.loads', r'fetch\(']
    risky_operations = sum(1 for pattern in risky_patterns if re.search(pattern, content, re.IGNORECASE))
    
    if risky_operations > 0 and not has_try:
        reasons.append(f"Missing error handling for {risky_operations} risky operation(s)")
    
    # Unimplemented functions
    if "pass" in content or "NotImplementedError" in content:
        reasons.append("Contains unimplemented function(s)")
    
    # Core module
    core_indicators = ["main", "core", "app", "server", "api", "pipeline"]
    if any(indicator in file_path.lower() for indicator in core_indicators):
        reasons.append("Core module (high impact)")
    
    # Recent activity
    recent_changes = sum(1 for commit in commits if file_path in commit.get("files", []))
    if recent_changes >= 3:
        reasons.append(f"High activity ({recent_changes} recent commits)")
    
    return reasons


def score_and_rank_files(
    source_files: List[Dict],
    file_contents: Dict[str, str],
    commits: List[Dict],
    top_k: int = 5
) -> List[Tuple[float, str, str, List[str]]]:
    """
    Score all files and return top K most suspicious
    
    Args:
        source_files: List of source file info dicts
        file_contents: Dictionary mapping file paths to contents
        commits: List of recent commits
        top_k: Number of top files to return
        
    Returns:
        List of tuples: (score, file_path, content, reasons)
        Sorted by score descending
    """
    scored_files = []
    
    for file_info in source_files:
        file_path = file_info.get("path", "")
        content = file_contents.get(file_path)
        
        if not content:
            continue
        
        score = score_file_suspiciousness(file_path, content, commits)
        reasons = get_suspiciousness_reasons(file_path, content, commits)
        
        # Only include files with non-zero scores
        if score > 0.0:
            scored_files.append((score, file_path, content, reasons))
    
    # Sort by score descending
    scored_files.sort(reverse=True, key=lambda x: x[0])
    
    return scored_files[:top_k]


# Made with Bob