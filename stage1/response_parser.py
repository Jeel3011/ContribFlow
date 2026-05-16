"""
Response parser for Stage 1 (Gap Finder)
Parses and validates LLM/Bob responses, handles imperfect JSON outputs
"""

import json
import re
from typing import Dict, List, Optional


# Valid values for output fields
VALID_IMPACTS = {"high", "medium", "low"}
VALID_CATEGORIES = {
    "error-handling",
    "test-coverage",
    "todo-fixme",
    "deprecated-deps",
    "unimplemented"
}


def extract_json_from_response(raw_response: str) -> Optional[str]:
    """
    Extract JSON from response that may contain markdown or extra text
    
    Args:
        raw_response: Raw response from LLM/Bob
        
    Returns:
        Extracted JSON string, or None if not found
    """
    # Try to find JSON in markdown code blocks
    markdown_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    match = re.search(markdown_pattern, raw_response)
    if match:
        return match.group(1)
    
    # Try to find raw JSON object
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, raw_response)
    if match:
        return match.group(0)
    
    return None


def normalize_impact(impact: str) -> str:
    """
    Normalize impact value to valid options
    
    Args:
        impact: Raw impact string
        
    Returns:
        Normalized impact: "high", "medium", or "low"
    """
    impact_lower = impact.lower().strip()
    
    if impact_lower in VALID_IMPACTS:
        return impact_lower
    
    # Handle common variations
    if impact_lower in ["critical", "severe", "major"]:
        return "high"
    elif impact_lower in ["moderate", "normal"]:
        return "medium"
    elif impact_lower in ["minor", "trivial", "small"]:
        return "low"
    
    # Default to medium if unclear
    return "medium"


def normalize_category(category: str) -> str:
    """
    Normalize category value to valid options
    
    Args:
        category: Raw category string
        
    Returns:
        Normalized category or original if valid
    """
    category_lower = category.lower().strip()
    
    if category_lower in VALID_CATEGORIES:
        return category_lower
    
    # Handle common variations
    category_map = {
        "error": "error-handling",
        "exception": "error-handling",
        "testing": "test-coverage",
        "tests": "test-coverage",
        "todo": "todo-fixme",
        "fixme": "todo-fixme",
        "deprecated": "deprecated-deps",
        "dependency": "deprecated-deps",
        "not-implemented": "unimplemented",
        "incomplete": "unimplemented"
    }
    
    for key, value in category_map.items():
        if key in category_lower:
            return value
    
    # Default to todo-fixme if unclear
    return "todo-fixme"


def validate_gap(gap: Dict) -> bool:
    """
    Validate a single gap entry
    
    Args:
        gap: Gap dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["title", "file", "impact", "category", "reasoning"]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in gap:
            return False
        if not gap[field] or not str(gap[field]).strip():
            return False
    
    return True


def parse_stage1_response(raw_response: str, repo: str) -> Dict:
    """
    Parse Stage 1 response from LLM/Bob
    
    Args:
        raw_response: Raw response string
        repo: Repository identifier (for fallback)
        
    Returns:
        Validated and normalized response dictionary
        
    Handles:
        - Markdown code blocks
        - Missing fields
        - Invalid field values
        - Malformed JSON
    """
    # Extract JSON from response
    json_str = extract_json_from_response(raw_response)
    
    if not json_str:
        # Return empty result if no JSON found
        return {
            "repo": repo,
            "gaps": [],
            "error": "No valid JSON found in response"
        }
    
    try:
        # Parse JSON
        data = json.loads(json_str)
        
        # Ensure required top-level fields
        if "repo" not in data:
            data["repo"] = repo
        
        if "gaps" not in data or not isinstance(data["gaps"], list):
            data["gaps"] = []
        
        # Validate and normalize each gap
        validated_gaps = []
        
        for gap in data["gaps"]:
            if not isinstance(gap, dict):
                continue
            
            # Skip invalid gaps
            if not validate_gap(gap):
                continue
            
            # Normalize fields
            normalized_gap = {
                "title": str(gap["title"]).strip(),
                "file": str(gap["file"]).strip(),
                "impact": normalize_impact(str(gap["impact"])),
                "category": normalize_category(str(gap["category"])),
                "reasoning": str(gap["reasoning"]).strip()
            }
            
            validated_gaps.append(normalized_gap)
        
        # Return validated response
        return {
            "repo": data["repo"],
            "gaps": validated_gaps
        }
        
    except json.JSONDecodeError as e:
        # Return error if JSON is malformed
        return {
            "repo": repo,
            "gaps": [],
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        # Catch any other errors
        return {
            "repo": repo,
            "gaps": [],
            "error": f"Parsing error: {str(e)}"
        }


def format_gaps_for_display(gaps: List[Dict]) -> str:
    """
    Format gaps for human-readable display
    
    Args:
        gaps: List of gap dictionaries
        
    Returns:
        Formatted string
    """
    if not gaps:
        return "No gaps identified."
    
    output = []
    
    for i, gap in enumerate(gaps, 1):
        output.append(f"\n{i}. {gap['title']}")
        output.append(f"   File: {gap['file']}")
        output.append(f"   Impact: {gap['impact'].upper()}")
        output.append(f"   Category: {gap['category']}")
        output.append(f"   Reasoning: {gap['reasoning']}")
    
    return "\n".join(output)


# Made with Bob