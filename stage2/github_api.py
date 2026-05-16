"""
GitHub API client for Stage 2 (Idea Deduplication)
Handles fetching issues and pull requests for semantic matching
"""

import os
import requests
from typing import List, Dict


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


def get_issues(owner_repo: str, max_issues: int = 50) -> List[Dict]:
    """
    Fetch issues from GitHub repository (excludes PRs)
    
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
        "state": "all",  # Include both open and closed
        "per_page": min(max_issues, 100),  # GitHub max is 100 per page
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
                "body": (item.get("body") or "")[:500],  # Trim to 500 chars
                "state": item["state"],
                "url": item["html_url"],
                "labels": [label["name"] for label in item.get("labels", [])]
            })
            
            if len(filtered_issues) >= max_issues:
                break
    
    return filtered_issues


def get_pull_requests(owner_repo: str, max_prs: int = 50) -> List[Dict]:
    """
    Fetch pull requests from GitHub repository
    
    Args:
        owner_repo: Repository in format "owner/repo"
        max_prs: Maximum number of PRs to fetch (default 50)
        
    Returns:
        List of PR dictionaries with fields: number, title, body, state, url, merged
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/pulls"
    params = {
        "state": "all",  # Include open, closed, and merged
        "per_page": min(max_prs, 100),
        "sort": "updated",
        "direction": "desc"
    }
    
    response = requests.get(url, headers=_get_headers(), params=params, timeout=10)
    _handle_response(response)
    
    prs = response.json()
    
    result = []
    for pr in prs[:max_prs]:
        result.append({
            "number": pr["number"],
            "title": pr["title"],
            "body": (pr.get("body") or "")[:500],  # Trim to 500 chars
            "state": pr["state"],
            "url": pr["html_url"],
            "merged": pr.get("merged", False)
        })
    
    return result

# Made with Bob
