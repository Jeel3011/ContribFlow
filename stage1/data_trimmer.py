"""
Data trimming and filtering utilities for Stage 1 (Gap Finder)
Reduces token usage by filtering irrelevant data before sending to Bob
"""

from typing import List, Dict

# Source file extensions to analyze
SOURCE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rb", ".php", ".cpp", ".c", ".h"}

# Directories to skip (tests, vendor, generated code)
SKIP_DIRS = {
    "test", "tests", "__tests__", "spec", "specs",
    "node_modules", "vendor", "dist", "build", "target",
    ".git", ".github", "venv", "env", "__pycache__",
    "coverage", "docs", "documentation", "examples"
}


def filter_source_files(tree: List[Dict]) -> List[Dict]:
    """
    Filter repository tree to source files only
    
    Args:
        tree: Repository tree from GitHub API
        
    Returns:
        Filtered list of source file nodes
        
    Filters out:
        - Non-source files (images, configs, etc.)
        - Test files and directories
        - Vendor/dependency directories
        - Generated code directories
    """
    source_files = []
    
    for item in tree:
        # Only process blob (file) types
        if item.get("type") != "blob":
            continue
        
        path = item.get("path", "")
        
        # Skip if path contains excluded directories
        path_parts = path.split("/")
        if any(skip_dir in path_parts for skip_dir in SKIP_DIRS):
            continue
        
        # Skip test files (common patterns)
        path_lower = path.lower()
        if any(test_pattern in path_lower for test_pattern in ["test_", "_test.", "spec.", ".test.", ".spec."]):
            continue
        
        # Only include source files
        if any(path.endswith(ext) for ext in SOURCE_EXTS):
            source_files.append({
                "path": path,
                "type": item.get("type")
            })
    
    return source_files


def trim_commits(commits: List[Dict], max_count: int = 50) -> List[Dict]:
    """
    Trim commits to reduce token usage
    
    Args:
        commits: List of commit dictionaries
        max_count: Maximum number of commits to keep
        
    Returns:
        Trimmed list of commits with essential fields only
    """
    trimmed = []
    
    for commit in commits[:max_count]:
        trimmed.append({
            "sha": commit.get("sha", "")[:7],  # Short SHA
            "message": commit.get("message", "")[:100],  # First 100 chars
            "author": commit.get("author", "Unknown"),
            "files": commit.get("files", [])[:10]  # Max 10 files per commit
        })
    
    return trimmed


def trim_issues(issues: List[Dict], max_count: int = 50) -> List[Dict]:
    """
    Trim issues to reduce token usage
    
    Args:
        issues: List of issue dictionaries
        max_count: Maximum number of issues to keep
        
    Returns:
        Trimmed list of issues with essential fields only
    """
    trimmed = []
    
    for issue in issues[:max_count]:
        trimmed.append({
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "body": issue.get("body", "")[:300],  # First 300 chars
            "labels": issue.get("labels", [])[:5]  # Max 5 labels
        })
    
    return trimmed


def trim_file_content(content: str, max_lines: int = 100) -> str:
    """
    Trim file content to first N lines
    
    Args:
        content: Full file content
        max_lines: Maximum number of lines to keep
        
    Returns:
        Trimmed content string
    """
    if not content:
        return ""
    
    lines = content.split("\n")
    
    if len(lines) <= max_lines:
        return content
    
    trimmed_lines = lines[:max_lines]
    return "\n".join(trimmed_lines) + f"\n... (truncated, {len(lines) - max_lines} more lines)"


def estimate_token_count(text: str) -> int:
    """
    Rough estimate of token count (1 token ≈ 4 characters)
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def build_context_summary(
    source_files: List[Dict],
    commits: List[Dict],
    issues: List[Dict]
) -> Dict:
    """
    Build a summary of repository context for token-efficient prompts
    
    Args:
        source_files: Filtered source files
        commits: Trimmed commits
        issues: Trimmed issues
        
    Returns:
        Dictionary with context summary
    """
    # Count files by extension
    ext_counts = {}
    for file_info in source_files:
        path = file_info.get("path", "")
        ext = path[path.rfind("."):] if "." in path else "unknown"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    
    # Get most active files from commits
    file_activity = {}
    for commit in commits:
        for file_path in commit.get("files", []):
            file_activity[file_path] = file_activity.get(file_path, 0) + 1
    
    most_active = sorted(file_activity.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_files": len(source_files),
        "file_types": ext_counts,
        "recent_commits": len(commits),
        "open_issues": len(issues),
        "most_active_files": [{"path": path, "changes": count} for path, count in most_active]
    }


# Made with Bob