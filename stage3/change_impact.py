"""
Stage 3: Change Impact Analysis
Analyzes which files depend on a target file to assess change impact.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set


def analyze_change_impact(repo_path: str, target_file: str) -> dict:
    """
    Analyze the impact of changes to a target file by finding all dependent files.
    
    Args:
        repo_path: Path to the repository root
        target_file: Path to the file being changed (relative to repo_path)
    
    Returns:
        dict with keys:
            - target: the file being changed
            - dependent_files: list of files that import it
            - affected_tests: list of test files among dependents
            - risk_level: "high" if >3 dependents, "medium" if 1-3, "low" if 0
    """
    repo_path_obj = Path(repo_path).resolve()
    target_file = str(target_file)
    
    # Normalize target file path
    if target_file.startswith(str(repo_path_obj)):
        target_relative = Path(target_file).relative_to(repo_path_obj)
    else:
        target_relative = Path(target_file)
    
    # Extract module name from target file
    target_module = _get_module_name(target_relative)
    
    # Find all dependent files
    dependent_files = []
    affected_tests = []
    
    for py_file in _walk_python_files(repo_path_obj):
        if py_file == target_relative:
            continue
            
        if _file_imports_target(repo_path_obj / py_file, target_module, target_relative):
            file_str = str(py_file)
            dependent_files.append(file_str)
            
            # Check if it's a test file
            if _is_test_file(py_file):
                affected_tests.append(file_str)
    
    # Determine risk level
    num_dependents = len(dependent_files)
    if num_dependents > 3:
        risk_level = "high"
    elif num_dependents >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "target": str(target_relative),
        "dependent_files": dependent_files,
        "affected_tests": affected_tests,
        "risk_level": risk_level
    }


def _walk_python_files(repo_path: Path) -> List[Path]:
    """
    Walk the repository and yield all Python files.
    Excludes common non-source directories.
    """
    exclude_dirs = {
        '__pycache__', '.git', 'venv', 'env', '.venv',
        'node_modules', 'dist', 'build', '.tox', '.pytest_cache'
    }
    
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    relative_path = file_path.relative_to(repo_path)
                    python_files.append(relative_path)
                except ValueError:
                    continue
    
    return python_files


def _get_module_name(file_path: Path) -> str:
    """
    Convert a file path to a Python module name.
    Example: src/utils/helper.py -> src.utils.helper
    """
    parts = list(file_path.parts)
    if parts[-1].endswith('.py'):
        parts[-1] = parts[-1][:-3]  # Remove .py extension
    
    return '.'.join(parts)


def _file_imports_target(file_path: Path, target_module: str, target_relative: Path) -> bool:
    """
    Check if a file imports the target module using AST parsing.
    
    Args:
        file_path: Path to the file to check
        target_module: Module name of the target (e.g., 'src.utils.helper')
        target_relative: Relative path of target file
    
    Returns:
        True if the file imports the target module
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _matches_target(alias.name, target_module):
                        return True
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and _matches_target(node.module, target_module):
                    return True
                
                # Handle relative imports
                if node.level > 0 and node.module is not None:
                    resolved = _resolve_relative_import(
                        file_path, node.module, node.level, target_relative
                    )
                    if resolved:
                        return True
        
        return False
    
    except (SyntaxError, UnicodeDecodeError, OSError):
        # Skip files that can't be parsed
        return False


def _matches_target(import_name: str, target_module: str) -> bool:
    """
    Check if an import name matches the target module.
    Handles both exact matches and parent module imports.
    """
    if import_name == target_module:
        return True
    
    # Check if target is a submodule of the import
    if target_module.startswith(import_name + '.'):
        return True
    
    return False


def _resolve_relative_import(
    current_file: Path, module: str, level: int, target_relative: Path
) -> bool:
    """
    Resolve relative imports and check if they reference the target.
    
    Args:
        current_file: The file containing the import
        module: The module being imported (can be None for 'from . import x')
        level: Number of dots in the relative import
        target_relative: The target file's relative path
    
    Returns:
        True if the relative import references the target
    """
    try:
        # Get the directory of the current file
        current_dir = current_file.parent
        
        # Go up 'level' directories
        for _ in range(level - 1):
            current_dir = current_dir.parent
        
        # Build the full module path
        if module:
            import_path = current_dir / module.replace('.', os.sep)
        else:
            import_path = current_dir
        
        # Check if this resolves to the target
        target_dir = target_relative.parent
        target_name = target_relative.stem
        
        if import_path == target_dir or import_path.name == target_name:
            return True
        
        return False
    
    except (ValueError, OSError):
        return False


def _is_test_file(file_path: Path) -> bool:
    """
    Check if a file is a test file based on naming conventions.
    """
    name = file_path.name.lower()
    parts = [p.lower() for p in file_path.parts]
    
    # Check filename patterns
    if name.startswith('test_') or name.endswith('_test.py'):
        return True
    
    # Check directory patterns
    if 'test' in parts or 'tests' in parts or '__tests__' in parts:
        return True
    
    return False

# Made with Bob
