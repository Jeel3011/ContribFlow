"""
Convention Sampler for Stage 4 (Pre-PR Quality Check)
Fetches representative files to establish repository coding conventions
"""

from typing import Dict, List
from collections import defaultdict
from stage4.github_api import get_tree, get_file_content, find_similar_files_in_tree


def _index_tree_by_directory(tree: List[Dict]) -> Dict[str, List[str]]:
    """Pre-index tree by directory for O(1) lookups."""
    by_dir: Dict[str, List[str]] = defaultdict(list)
    for item in tree:
        if item.get("type") == "blob":
            path = item["path"]
            parts = path.rsplit("/", 1)
            directory = parts[0] if len(parts) > 1 else ""
            by_dir[directory].append(path)
    return dict(by_dir)


def _find_similar_fast(
    tree_index: Dict[str, List[str]],
    target_file: str,
    max_results: int = 3
) -> List[str]:
    """O(1) lookup of similar files from pre-built directory index."""
    parts = target_file.rsplit("/", 1)
    directory = parts[0] if len(parts) > 1 else ""
    extension = "." + target_file.rsplit(".", 1)[-1] if "." in target_file else ""

    candidates = tree_index.get(directory, [])
    similar = [
        p for p in candidates
        if p != target_file and (not extension or p.endswith(extension))
    ]
    return similar[:max_results]


def sample_convention_files(
    owner_repo: str,
    changed_files: List[str],
    samples_per_file: int = 2,
    max_lines: int = 50
) -> Dict[str, List[Dict]]:
    """
    Sample convention files for each changed file
    
    Args:
        owner_repo: Repository in format "owner/repo"
        changed_files: List of changed file paths
        samples_per_file: Number of convention files to fetch per changed file
        max_lines: Maximum lines to include from each convention file
        
    Returns:
        Dictionary mapping changed file paths to convention samples:
        {
            "src/app.py": [
                {
                    "path": "src/utils.py",
                    "content": "...",
                    "lines": 45
                }
            ]
        }
    """
    print(f"[Stage 4] Fetching repository tree for convention sampling...")
    tree = get_tree(owner_repo)

    # Pre-index tree once — avoids O(n) linear scan per changed file
    tree_index = _index_tree_by_directory(tree)

    conventions = {}

    for changed_file in changed_files:
        print(f"[Stage 4] Sampling conventions for {changed_file}...")

        similar_files = _find_similar_fast(tree_index, changed_file, max_results=samples_per_file)

        samples = []
        for similar_file in similar_files:
            content = get_file_content(owner_repo, similar_file)

            if content:
                lines = content.split("\n")
                trimmed_content = "\n".join(lines[:max_lines])

                samples.append({
                    "path": similar_file,
                    "content": trimmed_content,
                    "lines": len(lines)
                })

                print(f"  ✓ Sampled {similar_file} ({len(lines)} lines)")

        conventions[changed_file] = samples

    return conventions


def extract_conventions_summary(conventions: Dict[str, List[Dict]]) -> Dict[str, str]:
    """
    Extract high-level convention patterns from sampled files
    
    Args:
        conventions: Output from sample_convention_files()
        
    Returns:
        Dictionary mapping changed files to convention summaries
    """
    summaries = {}
    
    for changed_file, samples in conventions.items():
        if not samples:
            summaries[changed_file] = "No convention files found"
            continue
        
        patterns = []
        
        # Analyze patterns across samples
        for sample in samples:
            content = sample["content"]
            
            # Check for docstring style
            if '"""' in content:
                patterns.append("Uses triple-quote docstrings")
            elif "'''" in content:
                patterns.append("Uses triple-quote docstrings (single quotes)")
            
            # Check for type hints
            if "->" in content:
                patterns.append("Uses type annotations")
            
            # Check for imports style
            if "from " in content and "import " in content:
                patterns.append("Uses 'from X import Y' style")
            
            # Check for class definitions
            if "class " in content:
                patterns.append("Defines classes")
            
            # Check for error handling
            if "try:" in content and "except" in content:
                patterns.append("Uses try/except error handling")
        
        # Deduplicate patterns
        unique_patterns = list(set(patterns))
        
        if unique_patterns:
            summaries[changed_file] = "; ".join(unique_patterns)
        else:
            summaries[changed_file] = "No clear patterns detected"
    
    return summaries


def format_conventions_for_prompt(conventions: Dict[str, List[Dict]]) -> str:
    """
    Format convention samples for inclusion in Bob prompt
    
    Args:
        conventions: Output from sample_convention_files()
        
    Returns:
        Formatted string for prompt
    """
    if not conventions:
        return "No convention files available."
    
    output = []
    
    for changed_file, samples in conventions.items():
        output.append(f"\n## Convention Context for {changed_file}\n")
        
        if not samples:
            output.append("No similar files found in repository.\n")
            continue
        
        output.append(f"Found {len(samples)} similar file(s) in the same directory:\n")
        
        for i, sample in enumerate(samples, 1):
            output.append(f"\n### Example {i}: {sample['path']}\n")
            output.append("```")
            output.append(sample['content'])
            if sample['lines'] > 50:
                output.append(f"\n... (truncated, full file is {sample['lines']} lines)")
            output.append("```\n")
    
    return "\n".join(output)


def get_convention_context(
    owner_repo: str,
    changed_files: List[str],
    samples_per_file: int = 2
) -> Dict:
    """
    Get complete convention context for changed files
    
    Args:
        owner_repo: Repository in format "owner/repo"
        changed_files: List of changed file paths
        samples_per_file: Number of samples per file
        
    Returns:
        Dictionary with conventions and summaries:
        {
            "conventions": {...},
            "summaries": {...},
            "formatted": "..."
        }
    """
    conventions = sample_convention_files(owner_repo, changed_files, samples_per_file)
    summaries = extract_conventions_summary(conventions)
    formatted = format_conventions_for_prompt(conventions)
    
    return {
        "conventions": conventions,
        "summaries": summaries,
        "formatted": formatted
    }


# Made with Bob