"""
GitHub API client for Stage 1 (Gap Finder)
Handles repository tree, commits, issues, and file content fetching
"""

import os
import requests
from typing import List, Dict, Optional


def _get_headers() -> dict:
    """Get GitHub API headers with optional authentication"""
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    return headers


def _handle_response(response: requests.Response) -> None:
    """Handle common GitHub API response errors"""
    if response.status_code == 403:
        raise Exception("GitHub rate limit hit")
    response.raise_for_status()


def get_tree(owner_repo: str) -> List[Dict]:
    """
    Fetch repository file tree from GitHub API
    
    Args:
        owner_repo: Repository in format "owner/repo"
        
    Returns:
        List of file nodes with 'path' and 'type' fields
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/git/trees/HEAD?recursive=1"
    
    response = requests.get(url, headers=_get_headers(), timeout=10)
    _handle_response(response)
    
    data = response.json()
    return data.get("tree", [])


def get_commits(owner_repo: str, max_commits: int = 50) -> List[Dict]:
    """
    Fetch recent commits from GitHub repository
    
    Args:
        owner_repo: Repository in format "owner/repo"
        max_commits: Maximum number of commits to fetch (default 50)
        
    Returns:
        List of commit dictionaries with fields: sha, message, author, date, files
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/commits"
    params = {
        "per_page": min(max_commits, 100),  # GitHub max is 100 per page
        "sort": "updated",
        "direction": "desc"
    }
    
    response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
    _handle_response(response)
    
    commits = response.json()
    
    result = []
    for commit in commits[:max_commits]:
        commit_data = commit.get("commit", {})
        result.append({
            "sha": commit.get("sha", "")[:7],  # Short SHA
            "message": commit_data.get("message", "")[:100],  # Trim to 100 chars
            "author": commit_data.get("author", {}).get("name", "Unknown"),
            "date": commit_data.get("author", {}).get("date", ""),
            "files": [f.get("filename", "") for f in commit.get("files", [])][:10]  # Max 10 files
        })
    
    return result


def get_issues(owner_repo: str, max_issues: int = 50) -> List[Dict]:
    """
    Fetch open issues from GitHub repository (excludes PRs)
    
    Args:
        owner_repo: Repository in format "owner/repo"
        max_issues: Maximum number of issues to fetch (default 50)
        
    Returns:
        List of issue dictionaries with fields: number, title, body, state, url, labels
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/issues"
    params = {
        "state": "open",  # Only open issues for gap finding
        "per_page": min(max_issues, 100),
        "sort": "updated",
        "direction": "desc"
    }
    
    response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
    _handle_response(response)
    
    issues = response.json()
    
    # Filter out pull requests (GitHub issues endpoint returns both)
    filtered_issues = []
    for item in issues:
        # PRs have a 'pull_request' key
        if "pull_request" not in item:
            filtered_issues.append({
                "number": item["number"],
                "title": item["title"],
                "body": (item.get("body") or "")[:300],  # Trim to 300 chars
                "state": item["state"],
                "url": item["html_url"],
                "labels": [label["name"] for label in item.get("labels", [])]
            })
            
            if len(filtered_issues) >= max_issues:
                break
    
    return filtered_issues


def get_file_content(owner_repo: str, path: str) -> Optional[str]:
    """
    Fetch file content from GitHub API
    
    Args:
        owner_repo: Repository in format "owner/repo"
        path: File path within repository
        
    Returns:
        Decoded file content as string, or None on error
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/contents/{path}"
    
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        
        if response.status_code == 403:
            raise Exception("GitHub rate limit hit")
        
        response.raise_for_status()
        
        data = response.json()
        
        # GitHub API returns base64-encoded content
        import base64
        content = data.get("content", "")
        if content:
            decoded = base64.b64decode(content).decode("utf-8")
            return decoded
        
        return None
        
    except Exception as e:
        # Re-raise rate limit exceptions
        if "rate limit" in str(e).lower():
            raise
        # Return None for other errors (file too large, binary, etc.)
        return None


# Made with Bob