"""
Semantic matching module for Stage 2 (Idea Deduplication)
Uses sentence transformers to compute similarity between contribution ideas and existing issues/PRs
"""

from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# Global model instance (singleton pattern for efficiency)
_model = None


def _get_model() -> SentenceTransformer:
    """
    Get or initialize the sentence transformer model
    Uses all-MiniLM-L6-v2 for fast, lightweight embeddings
    """
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def compute_embeddings(texts: List[str]) -> np.ndarray:
    """
    Compute embeddings for a list of texts
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        Numpy array of embeddings (shape: [len(texts), embedding_dim])
    """
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings


def compute_similarity(idea_embedding: np.ndarray, item_embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between idea and multiple items
    
    Args:
        idea_embedding: Single embedding vector (shape: [embedding_dim])
        item_embeddings: Multiple embedding vectors (shape: [n_items, embedding_dim])
        
    Returns:
        Array of similarity scores (shape: [n_items])
    """
    # Reshape idea_embedding to 2D for sklearn
    idea_2d = idea_embedding.reshape(1, -1)
    similarities = cosine_similarity(idea_2d, item_embeddings)[0]
    return similarities


def find_matches(
    idea: str,
    issues: List[Dict],
    prs: List[Dict],
    threshold: float = 0.5
) -> List[Dict]:
    """
    Find semantic matches between contribution idea and existing issues/PRs
    
    Args:
        idea: Contribution idea text
        issues: List of issue dictionaries with 'title', 'body', 'number', etc.
        prs: List of PR dictionaries with 'title', 'body', 'number', etc.
        threshold: Minimum similarity score to consider a match (default 0.5)
        
    Returns:
        List of matches sorted by similarity (highest first), each containing:
        - type: "issue" or "pr"
        - number: Issue/PR number
        - title: Issue/PR title
        - url: GitHub URL
        - similarity: Similarity score (0.0-1.0)
        - state: "open" or "closed"
        - merged: True/False (PRs only)
    """
    # Combine issues and PRs for batch processing
    all_items = []
    item_metadata = []
    
    for issue in issues:
        # Combine title and body for better semantic matching
        text = f"{issue['title']} {issue['body']}"
        all_items.append(text)
        item_metadata.append({
            "type": "issue",
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["url"],
            "state": issue["state"],
            "labels": issue.get("labels", [])
        })
    
    for pr in prs:
        text = f"{pr['title']} {pr['body']}"
        all_items.append(text)
        item_metadata.append({
            "type": "pr",
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["url"],
            "state": pr["state"],
            "merged": pr.get("merged", False)
        })
    
    # Return empty list if no items to match
    if not all_items:
        return []
    
    # Compute embeddings
    idea_embedding = compute_embeddings([idea])[0]
    item_embeddings = compute_embeddings(all_items)
    
    # Compute similarities
    similarities = compute_similarity(idea_embedding, item_embeddings)
    
    # Filter and sort matches
    matches = []
    for idx, similarity in enumerate(similarities):
        if similarity >= threshold:
            match = item_metadata[idx].copy()
            match["similarity"] = float(similarity)
            matches.append(match)
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    return matches


def get_top_matches(
    idea: str,
    issues: List[Dict],
    prs: List[Dict],
    top_k: int = 5,
    threshold: float = 0.5
) -> List[Dict]:
    """
    Get top K semantic matches for Bob prompt
    
    Args:
        idea: Contribution idea text
        issues: List of issue dictionaries
        prs: List of PR dictionaries
        top_k: Maximum number of matches to return (default 5)
        threshold: Minimum similarity score (default 0.5)
        
    Returns:
        Top K matches sorted by similarity
    """
    matches = find_matches(idea, issues, prs, threshold)
    return matches[:top_k]

# Made with Bob
