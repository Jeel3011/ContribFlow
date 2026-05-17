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


class RateLimitException(Exception):
    """Raised when GitHub rate limit is hit so callers can decide how to handle it."""
    def __init__(self, message: str, wait_seconds: float = 60.0):
        super().__init__(message)
        self.wait_seconds = wait_seconds


class RateLimitTracker:
    """Thread-safe rate limit state tracker."""

    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self._remaining = 30
        self._reset_at: Optional[float] = None

    def update(self, headers: dict) -> None:
        with self._lock:
            remaining = headers.get("X-RateLimit-Remaining")
            reset = headers.get("X-RateLimit-Reset")
            if remaining is not None:
                try:
                    self._remaining = int(remaining)
                except ValueError:
                    pass
            if reset is not None:
                try:
                    self._reset_at = float(reset)
                except ValueError:
                    pass

    def seconds_until_reset(self) -> float:
        if self._reset_at is None:
            return 60.0
        return max(0.0, self._reset_at - time.time())

    def should_wait(self) -> bool:
        return self._remaining < 2


_search_rate_tracker = RateLimitTracker()


class GitHubSearchClient:
    """Client for GitHub Code Search API with rate limit handling"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.rate_limit_remaining = 30
        self.rate_limit_reset = None

    def search_code(
        self,
        query: str,
        repo: str,
        language: str = "python",
        max_results: int = 30
    ) -> List[Dict]:
        """
        Search code using GitHub's semantic search.

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

        # Check rate limit state BEFORE making request.
        # Raise so the async caller can handle waiting in a non-blocking way
        # (this function always runs inside run_in_executor, so raising here
        # propagates cleanly back to the async route handler).
        if _search_rate_tracker.should_wait():
            wait = _search_rate_tracker.seconds_until_reset()
            raise RateLimitException(
                f"GitHub search rate limit low, reset in {wait:.0f}s",
                wait_seconds=wait
            )

        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)

                # Update tracker with fresh header info
                _search_rate_tracker.update(response.headers)
                self.rate_limit_remaining = int(
                    response.headers.get("X-RateLimit-Remaining", 30)
                )
                reset_ts = response.headers.get("X-RateLimit-Reset")
                if reset_ts:
                    self.rate_limit_reset = int(reset_ts)

                if response.status_code == 403:
                    wait = _search_rate_tracker.seconds_until_reset()
                    logger.error(
                        f"GitHub rate limit exceeded (attempt {attempt+1}/{retries}). "
                        f"Resets in {wait:.0f}s"
                    )
                    # Raise immediately — never time.sleep() on async thread
                    raise RateLimitException(
                        f"GitHub Code Search rate limited. Resets in {wait:.0f}s.",
                        wait_seconds=wait
                    )

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

            except RateLimitException:
                raise  # Don't retry rate-limit errors — propagate immediately
            except requests.exceptions.RequestException as e:
                logger.error(f"GitHub search failed: {e}")
                if attempt == retries - 1:
                    return []
                # Small retry delay. This function always runs inside
                # run_in_executor so sleeping here blocks only the worker
                # thread, NOT the async event loop.
                time.sleep(2)

        return []

    def multi_term_search(
        self,
        terms: List[str],
        repo: str,
        language: str = "python",
        max_per_term: int = 20
    ) -> List[Dict]:
        """
        Search multiple terms and merge results.
        Deduplicates by file path and ranks by score.

        Args:
            terms: List of search terms (use up to 8 for best coverage)
            repo: Repository identifier
            language: Programming language
            max_per_term: Max results per search term (20 is optimal per budget analysis)

        Returns:
            Deduplicated and sorted list of results
        """
        all_results = {}

        for term in terms:
            if not term or len(term) < 2:
                continue

            try:
                results = self.search_code(term, repo, language, max_per_term)
            except RateLimitException as e:
                logger.warning(
                    f"Rate limited during multi_term_search for '{term}': {e}. Stopping early."
                )
                break

            for result in results:
                path = result["path"]
                if path not in all_results:
                    all_results[path] = result
                    all_results[path]["matched_terms"] = [term]
                else:
                    all_results[path]["score"] = max(
                        all_results[path]["score"],
                        result["score"]
                    )
                    all_results[path]["matched_terms"].append(term)

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
        Find all files that import a specific module or file path.

        Args:
            module_name: Module to search for (e.g., "config", "app/types/config.py")
            repo: Repository identifier
            language: Programming language

        Returns:
            List of files that import the module
        """
        if module_name.endswith(".py"):
            module_name = module_name.replace("/", ".").removesuffix(".py")

        return self.search_code(module_name, repo, language, max_results=30)


def extract_keywords_from_description(description: str) -> List[str]:
    """
    Extract potential search keywords from change description.

    Args:
        description: Change description text

    Returns:
        List of keywords to search for
    """
    import re

    quoted = re.findall(r'["`]([^"`]+)["`]', description)
    camel_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', description)
    tech_terms = re.findall(
        r'\b(?:class|function|method|type|config|service|node|handler|client|server)\b',
        description.lower()
    )

    keywords = list(set(quoted + camel_case + tech_terms))
    keywords = [k for k in keywords if len(k) >= 3 and k.lower() not in {'the', 'and', 'for', 'with'}]

    return keywords[:15]


# Made with Bob
