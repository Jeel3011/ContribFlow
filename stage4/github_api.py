"""
GitHub API client for Stage 4 (Pre-PR Quality Check)
Handles repository tree fetching and file content retrieval
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
        _handle_response(response)
        
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
        # Return None for other errors (file not found, etc.)
        return None


def get_directory_files(owner_repo: str, directory: str, extension: str = "") -> List[Dict]:
    """
    Fetch all files in a directory with optional extension filter
    
    Args:
        owner_repo: Repository in format "owner/repo"
        directory: Directory path within repository
        extension: Optional file extension filter (e.g., ".py")
        
    Returns:
        List of file dictionaries with 'name', 'path', 'type' fields
        
    Raises:
        Exception: If GitHub rate limit is hit (403 status)
    """
    url = f"https://api.github.com/repos/{owner_repo}/contents/{directory}"
    
    try:
        response = requests.get(url, headers=_get_headers(), timeout=10)
        _handle_response(response)
        
        data = response.json()
        
        # Filter to files only (not directories)
        files = [item for item in data if item.get("type") == "file"]
        
        # Apply extension filter if provided
        if extension:
            files = [f for f in files if f.get("name", "").endswith(extension)]
        
        return files
        
    except Exception as e:
        # Re-raise rate limit exceptions
        if "rate limit" in str(e).lower():
            raise
        # Return empty list for other errors
        return []


def find_similar_files_in_tree(tree: List[Dict], target_file: str, max_results: int = 3) -> List[str]:
    """
    Find files similar to target file (same directory and extension)
    
    Args:
        tree: Repository tree from get_tree()
        target_file: Target file path (e.g., "src/app.py")
        max_results: Maximum number of similar files to return
        
    Returns:
        List of file paths similar to target
    """
    # Extract directory and extension from target
    parts = target_file.rsplit("/", 1)
    if len(parts) == 2:
        directory = parts[0]
        filename = parts[1]
    else:
        directory = ""
        filename = target_file
    
    # Get extension
    extension = ""
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[1]
    
    # Find files in same directory with same extension
    similar = []
    for item in tree:
        path = item.get("path", "")
        item_type = item.get("type", "")
        
        # Skip if not a file
        if item_type != "blob":
            continue
        
        # Skip the target file itself
        if path == target_file:
            continue
        
        # Check if in same directory
        if directory:
            if not path.startswith(directory + "/"):
                continue
        
        # Check if same extension
        if extension and not path.endswith(extension):
            continue
        
        similar.append(path)
        
        # Limit results
        if len(similar) >= max_results:
            break
    
    return similar


# Made with Bob