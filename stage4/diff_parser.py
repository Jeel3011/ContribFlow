"""
Diff Parser for Stage 4 (Pre-PR Quality Check)
Parses unified git diffs into structured format for analysis
"""

import re
from typing import Dict, List, Optional


# Language detection mapping
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".sql": "sql",
}


def detect_language(file_path: str) -> str:
    """
    Detect programming language from file extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name (e.g., "python", "javascript") or "unknown"
    """
    for ext, lang in LANGUAGE_MAP.items():
        if file_path.endswith(ext):
            return lang
    return "unknown"


def parse_diff(diff_text: str) -> Dict:
    """
    Parse unified git diff into structured format
    
    Args:
        diff_text: Raw unified diff text
        
    Returns:
        Dictionary containing:
        {
            "files": [
                {
                    "path": "src/app.py",
                    "old_path": "src/app.py",  # For renames
                    "language": "python",
                    "status": "modified",  # modified, added, deleted, renamed
                    "additions": ["def new_func():", "    pass"],
                    "deletions": ["# old code"],
                    "chunks": [
                        {
                            "old_start": 10,
                            "old_count": 5,
                            "new_start": 10,
                            "new_count": 7,
                            "lines": [
                                {"type": "context", "content": "import os", "old_line": 10, "new_line": 10},
                                {"type": "addition", "content": "import sys", "new_line": 11},
                                {"type": "deletion", "content": "# comment", "old_line": 11}
                            ]
                        }
                    ]
                }
            ],
            "stats": {
                "files_changed": 1,
                "additions": 2,
                "deletions": 1
            }
        }
    """
    files = []
    current_file = None
    current_chunk = None
    
    lines = diff_text.split("\n")
    
    total_additions = 0
    total_deletions = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # File header: diff --git a/path b/path
        if line.startswith("diff --git"):
            # Save previous file if exists
            if current_file:
                files.append(current_file)
            
            # Extract file paths
            match = re.search(r'a/(.+?)\s+b/(.+)', line)
            if match:
                old_path = match.group(1)
                new_path = match.group(2)
                
                current_file = {
                    "path": new_path,
                    "old_path": old_path,
                    "language": detect_language(new_path),
                    "status": "modified",
                    "additions": [],
                    "deletions": [],
                    "chunks": []
                }
                current_chunk = None
        
        # Old file marker: --- a/path or --- /dev/null
        elif line.startswith("---"):
            if current_file and "/dev/null" in line:
                current_file["status"] = "added"
        
        # New file marker: +++ b/path or +++ /dev/null
        elif line.startswith("+++"):
            if current_file and "/dev/null" in line:
                current_file["status"] = "deleted"
        
        # Chunk header: @@ -10,5 +10,7 @@
        elif line.startswith("@@"):
            match = re.search(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            if match and current_file:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                current_chunk = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": []
                }
                current_file["chunks"].append(current_chunk)
        
        # Content lines
        elif current_chunk is not None and current_file:
            if line.startswith("+") and not line.startswith("+++"):
                # Addition
                content = line[1:]  # Remove + prefix
                current_file["additions"].append(content)
                current_chunk["lines"].append({
                    "type": "addition",
                    "content": content,
                    "new_line": len([l for l in current_chunk["lines"] if l["type"] in ["context", "addition"]]) + current_chunk["new_start"]
                })
                total_additions += 1
                
            elif line.startswith("-") and not line.startswith("---"):
                # Deletion
                content = line[1:]  # Remove - prefix
                current_file["deletions"].append(content)
                current_chunk["lines"].append({
                    "type": "deletion",
                    "content": content,
                    "old_line": len([l for l in current_chunk["lines"] if l["type"] in ["context", "deletion"]]) + current_chunk["old_start"]
                })
                total_deletions += 1
                
            elif line.startswith(" "):
                # Context line (unchanged)
                content = line[1:]  # Remove space prefix
                old_line = len([l for l in current_chunk["lines"] if l["type"] in ["context", "deletion"]]) + current_chunk["old_start"]
                new_line = len([l for l in current_chunk["lines"] if l["type"] in ["context", "addition"]]) + current_chunk["new_start"]
                current_chunk["lines"].append({
                    "type": "context",
                    "content": content,
                    "old_line": old_line,
                    "new_line": new_line
                })
        
        i += 1
    
    # Save last file
    if current_file:
        files.append(current_file)
    
    # Detect renames
    for file in files:
        if file["old_path"] != file["path"]:
            file["status"] = "renamed"
    
    return {
        "files": files,
        "stats": {
            "files_changed": len(files),
            "additions": total_additions,
            "deletions": total_deletions
        }
    }


def extract_added_lines(parsed_diff: Dict) -> Dict[str, List[str]]:
    """
    Extract only added lines from parsed diff
    
    Args:
        parsed_diff: Output from parse_diff()
        
    Returns:
        Dictionary mapping file paths to lists of added lines
    """
    result = {}
    
    for file in parsed_diff["files"]:
        if file["additions"]:
            result[file["path"]] = file["additions"]
    
    return result


def extract_deleted_lines(parsed_diff: Dict) -> Dict[str, List[str]]:
    """
    Extract only deleted lines from parsed diff
    
    Args:
        parsed_diff: Output from parse_diff()
        
    Returns:
        Dictionary mapping file paths to lists of deleted lines
    """
    result = {}
    
    for file in parsed_diff["files"]:
        if file["deletions"]:
            result[file["path"]] = file["deletions"]
    
    return result


def get_changed_files(parsed_diff: Dict) -> List[str]:
    """
    Get list of changed file paths
    
    Args:
        parsed_diff: Output from parse_diff()
        
    Returns:
        List of file paths
    """
    return [file["path"] for file in parsed_diff["files"]]


def filter_by_language(parsed_diff: Dict, language: str) -> Dict:
    """
    Filter diff to only include files of a specific language
    
    Args:
        parsed_diff: Output from parse_diff()
        language: Language to filter by (e.g., "python")
        
    Returns:
        Filtered diff dictionary
    """
    filtered_files = [
        file for file in parsed_diff["files"]
        if file["language"] == language
    ]
    
    return {
        "files": filtered_files,
        "stats": {
            "files_changed": len(filtered_files),
            "additions": sum(len(f["additions"]) for f in filtered_files),
            "deletions": sum(len(f["deletions"]) for f in filtered_files)
        }
    }


def format_diff_summary(parsed_diff: Dict) -> str:
    """
    Format diff into human-readable summary
    
    Args:
        parsed_diff: Output from parse_diff()
        
    Returns:
        Formatted summary string
    """
    stats = parsed_diff["stats"]
    files = parsed_diff["files"]
    
    summary = f"Changed {stats['files_changed']} file(s): "
    summary += f"+{stats['additions']} additions, -{stats['deletions']} deletions\n\n"
    
    for file in files:
        summary += f"• {file['path']} ({file['status']}, {file['language']})\n"
        summary += f"  +{len(file['additions'])} -{len(file['deletions'])}\n"
    
    return summary


# Made with Bob