"""
GitHub Code Search API integration
Provides semantic code search across repositories
"""

import requests
import time
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GitHubSearchClient:
    """Client for GitHub Code Search API with rate limit handling"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.rate_limit_remaining = 30  # Code search: 30 req/min
        self.rate_limit_reset = None
        
    def search_code(
        self, 
        query: str, 
        repo: str, 
        language: str = "python",
        max_results: int = 30
    ) -> List[Dict]:
        """
        Search code using GitHub's semantic search
        
        Args:
            query: Search term (e.g., "RunnableConfig")
            repo: Repository in format "owner/repo"
            language: Programming language filter
            max_results: Maximum results to return
            
        Returns:
            List of {path, score, url, matches}
        """
        url = f"{self.base_url}/search/code"
        params = {
            "q": f"{query} repo:{repo} language:{language}",
            "per_page": min(max_results, 100)
        }
        
        headers = {
            "Accept": "application/vnd.github.v3.text-match+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
            
        retries = 3
        for attempt in range(retries):
            # Rate limit handling before request
            if self.rate_limit_remaining < 3:
                wait_time = 60
                if self.rate_limit_reset:
                    wait_time = max(0, self.rate_limit_reset - time.time())
                logger.warning(f"Rate limit low, waiting {wait_time}s")
                time.sleep(wait_time + 1)
                self.rate_limit_remaining = 30
                
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                # Update rate limit info
                self.rate_limit_remaining = int(
                    response.headers.get("X-RateLimit-Remaining", 30)
                )
                reset_timestamp = response.headers.get("X-RateLimit-Reset")
                if reset_timestamp:
                    self.rate_limit_reset = int(reset_timestamp)
                
                if response.status_code == 403:
                    logger.error(f"GitHub rate limit exceeded (attempt {attempt+1}/{retries})")
                    wait_time = max(0, self.rate_limit_reset - time.time()) if self.rate_limit_reset else 60
                    logger.warning(f"Sleeping for {wait_time}s before retry")
                    time.sleep(wait_time + 1)
                    continue
                
                if response.status_code == 422:
                    logger.warning(f"Invalid search query: {query}")
                    return []
                    
                response.raise_for_status()
                
                results = response.json().get("items", [])
                
                return [
                    {
                        "path": item["path"],
                        "score": item.get("score", 0),
                        "url": item.get("html_url", ""),
                        "matches": item.get("text_matches", [])
                    }
                    for item in results
                ]
                
            except requests.exceptions.RequestException as e:
                logger.error(f"GitHub search failed: {e}")
                if attempt == retries - 1:
                    return []
                time.sleep(5)
                
        return []
    
    def multi_term_search(
        self,
        terms: List[str],
        repo: str,
        language: str = "python",
        max_per_term: int = 20
    ) -> List[Dict]:
        """
        Search multiple terms and merge results
        Deduplicates by file path and ranks by score
        
        Args:
            terms: List of search terms
            repo: Repository identifier
            language: Programming language
            max_per_term: Max results per search term
            
        Returns:
            Deduplicated and sorted list of results
        """
        all_results = {}
        
        for term in terms:
            if not term or len(term) < 2:
                continue
                
            results = self.search_code(term, repo, language, max_per_term)
            
            for result in results:
                path = result["path"]
                if path not in all_results:
                    all_results[path] = result
                    all_results[path]["matched_terms"] = [term]
                else:
                    # Merge scores (take max)
                    all_results[path]["score"] = max(
                        all_results[path]["score"],
                        result["score"]
                    )
                    all_results[path]["matched_terms"].append(term)
        
        # Sort by score descending, then by number of matched terms
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: (x["score"], len(x.get("matched_terms", []))),
            reverse=True
        )
        
        return sorted_results
    
    def search_imports(
        self,
        module_name: str,
        repo: str,
        language: str = "python"
    ) -> List[Dict]:
        """
        Find all files that import a specific module or file path
        
        Args:
            module_name: Module to search for (e.g., "config", "app/types/config.py")
            repo: Repository identifier
            language: Programming language
            
        Returns:
            List of files that import the module
        """
        # Convert file path to python module if needed
        if module_name.endswith(".py"):
            module_name = module_name.replace("/", ".").removesuffix(".py")
            
        # For python, just searching the module name is most effective with GitHub search
        # as punctuation like "from" and "import" are often ignored or split.
        return self.search_code(module_name, repo, language, max_results=30)


def extract_keywords_from_description(description: str) -> List[str]:
    """
    Extract potential search keywords from change description
    
    Args:
        description: Change description text
        
    Returns:
        List of keywords to search for
    """
    import re
    
    # Extract quoted strings
    quoted = re.findall(r'["`]([^"`]+)["`]', description)
    
    # Extract CamelCase identifiers
    camel_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', description)
    
    # Extract common technical terms
    tech_terms = re.findall(
        r'\b(?:class|function|method|type|config|service|node|handler|client|server)\b',
        description.lower()
    )
    
    # Combine and deduplicate
    keywords = list(set(quoted + camel_case + tech_terms))
    
    # Filter out very short or common words
    keywords = [k for k in keywords if len(k) >= 3 and k.lower() not in {'the', 'and', 'for', 'with'}]
    
    return keywords[:15]  # Limit to top 15


# Example usage
if __name__ == "__main__":
    client = GitHubSearchClient()
    
    # Test search
    results = client.search_code(
        "RunnableConfig",
        "Tracer-Cloud/opensre",
        language="python"
    )
    
    print(f"Found {len(results)} files")
    for r in results[:5]:
        print(f"  - {r['path']} (score: {r['score']})")

# Made with Bob
