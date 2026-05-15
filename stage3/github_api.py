"""
GitHub API client for Stage 3 (Change Impact Analysis)
Handles repository tree fetching and file content retrieval
"""

import os
import requests
from typing import Optional


def get_tree(owner_repo: str) -> list[dict]:
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
    
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 403:
        raise Exception("GitHub rate limit hit")
    
    response.raise_for_status()
    
    data = response.json()
    return data.get("tree", [])


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
    
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 403:
            raise Exception("GitHub rate limit hit")
        
        response.raise_for_status()
        
        data = response.json()
        
        # GitHub API returns base64-encoded content
        import base64
        content = data.get("content", "")
        if content:
            return base64.b64decode(content).decode("utf-8")
        
        return None
        
    except Exception as e:
        # Re-raise rate limit exceptions
        if "rate limit" in str(e).lower():
            raise
        # Return None for other errors
        return None
