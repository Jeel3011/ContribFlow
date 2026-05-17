"""
Suspiciousness scoring heuristic for Stage 1 (Gap Finder)
Pre-selects top suspicious files BEFORE Bob to save tokens (AGENTS.md requirement)
"""

import re
import math
from typing import List, Dict, Tuple


def score_file_suspiciousness(
    file_path: str,
    content: str,
    commits: List[Dict]
) -> float:
    """
    Score file suspiciousness based on multiple heuristics.

    Scoring uses density-based factors so many similar files don't tie
    at the same score (previous flat +0.1 cap caused plateau for core modules).

    Args:
        file_path: Path to the file
        content: File content
        commits: List of recent commits

    Returns:
        Suspiciousness score (0.0–1.0), higher = more likely to have gaps
    """
    score = 0.0
    content_lower = content.lower()
    lines = content.split("\n")
    total_lines = max(len(lines), 1)

    # 1. TODO/FIXME density (+0.3 max) — normalize by file length
    todo_count = content_lower.count("todo") + content_lower.count("fixme")
    hack_count = content_lower.count("hack") + content_lower.count("xxx")
    total_markers = todo_count + hack_count
    todo_density = total_markers / total_lines
    score += min(todo_density * 10, 0.3)

    # 2. Error handling coverage — ratio of try blocks to risky operations (+0.25 max)
    risky_ops = len(re.findall(
        r'(requests\.|open\(|json\.loads|json\.parse|subprocess\.|exec\(|eval\(|fetch\(|axios\.)',
        content
    ))
    try_blocks = len(re.findall(r'\btry\s*[:{]', content))
    if risky_ops > 0:
        coverage = try_blocks / risky_ops
        score += (1 - min(coverage, 1.0)) * 0.25

    # 3. Unimplemented function ratio (+0.15 max)
    total_defs = len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
    unimpl = len(re.findall(r'(raise NotImplementedError|\bpass\b)', content))
    if total_defs > 0:
        score += min((unimpl / total_defs) * 0.3, 0.15)

    # 4. Deprecated imports (+0.2 max)
    deprecated = [
        "optparse", "imp", "md5", "sha", "sets", "string.atoi",
        "request", "node-uuid"
    ]
    deprecated_found = sum(
        1 for dep in deprecated
        if f"import {dep}" in content_lower or f"require('{dep}')" in content_lower
    )
    if deprecated_found > 0:
        score += min(deprecated_found * 0.1, 0.2)

    # 5. Commit frequency — log scale prevents runaway scoring (+0.1 max)
    recent_changes = sum(1 for c in commits if file_path in c.get("files", []))
    if recent_changes > 0:
        score += min(math.log(recent_changes + 1) * 0.05, 0.1)

    # 6. File size — larger files are harder to maintain (+0.1 max)
    if total_lines > 300:
        score += 0.05
    if total_lines > 600:
        score += 0.05

    # 7. Missing documentation (+0.05)
    has_docstring = '"""' in content or "'''" in content or "/**" in content
    comment_ratio = (content.count("#") + content.count("//")) / total_lines
    if not has_docstring and comment_ratio < 0.05:
        score += 0.05

    return min(score, 1.0)


def score_by_filename_only(file_path: str, commits: List[Dict]) -> float:
    """
    Pass 1 scorer — no content fetch required.
    Uses filename heuristics and commit frequency to narrow candidates.
    """
    score = 0.0
    path_lower = file_path.lower()

    core_indicators = [
        "main", "core", "app", "server", "api", "pipeline",
        "service", "controller", "handler", "manager", "engine"
    ]
    if any(ind in path_lower for ind in core_indicators):
        score += 0.15

    # Extension bonuses
    if file_path.endswith(".py") or file_path.endswith(".js") or file_path.endswith(".ts"):
        score += 0.05

    # Commit frequency (log scale)
    recent_changes = sum(1 for c in commits if file_path in c.get("files", []))
    if recent_changes > 0:
        score += min(math.log(recent_changes + 1) * 0.05, 0.1)

    return score


def get_suspiciousness_reasons(
    file_path: str,
    content: str,
    commits: List[Dict]
) -> List[str]:
    """
    Get human-readable reasons for suspiciousness score.
    """
    reasons = []
    content_lower = content.lower()

    todo_count = content_lower.count("todo") + content_lower.count("fixme")
    if todo_count > 0:
        reasons.append(f"{todo_count} TODO/FIXME comment(s) found")

    has_try = "try:" in content_lower or "try {" in content_lower
    risky_ops = sum(1 for p in [r'open\s*\(', r'requests\.', r'json\.loads', r'fetch\(']
                    if re.search(p, content, re.IGNORECASE))
    if risky_ops > 0 and not has_try:
        reasons.append(f"Missing error handling for {risky_ops} risky operation(s)")

    if "pass" in content or "NotImplementedError" in content:
        reasons.append("Contains unimplemented function(s)")

    core_indicators = ["main", "core", "app", "server", "api", "pipeline"]
    if any(ind in file_path.lower() for ind in core_indicators):
        reasons.append("Core module (high impact)")

    recent_changes = sum(1 for c in commits if file_path in c.get("files", []))
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
    Two-pass scorer:
      Pass 1 — rank by filename + commit frequency only (no content fetch)
      Pass 2 — full content scoring on top 20 candidates

    Args:
        source_files: List of source file info dicts
        file_contents: Dictionary mapping file paths to contents
        commits: List of recent commits
        top_k: Number of top files to return

    Returns:
        List of tuples: (score, file_path, content, reasons) sorted by score desc
    """
    # Pass 1: score without content — eliminates most files cheaply
    pass1_scores = []
    for file_info in source_files:
        path = file_info.get("path", "")
        s = score_by_filename_only(path, commits)
        pass1_scores.append((s, path))

    pass1_scores.sort(reverse=True, key=lambda x: x[0])
    top_candidates = [path for _, path in pass1_scores[:20]]

    # Pass 2: full content scoring on top 20 only
    scored_files = []
    for path in top_candidates:
        content = file_contents.get(path)
        if not content:
            continue

        score = score_file_suspiciousness(path, content, commits)
        reasons = get_suspiciousness_reasons(path, content, commits)

        if score > 0.0:
            scored_files.append((score, path, content, reasons))

    scored_files.sort(reverse=True, key=lambda x: x[0])
    return scored_files[:top_k]


# Made with Bob