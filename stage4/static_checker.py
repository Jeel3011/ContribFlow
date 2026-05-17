"""
Static Code Checker for Stage 4 (Pre-PR Quality Check)
Runs deterministic checks BEFORE Bob to save tokens
"""

import asyncio
import re
import json
import os
import tempfile
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def safe_line_number(line_str) -> int:
    """Extract integer from various line formats like '42', '42-50', '~45', 'L42'."""
    try:
        return int(str(line_str).split("-")[0].strip().lstrip("~").lstrip("L"))
    except (ValueError, AttributeError):
        return 0


def run_static_checks(parsed_diff: Dict, include_info: bool = False) -> List[Dict]:
    """
    Run all static checks on parsed diff.

    Args:
        parsed_diff: Output from diff_parser.parse_diff()
        include_info: If True, always include info-level issues. If False (default),
                      info-level issues are only returned when no errors/warnings exist.

    Returns:
        List of issues sorted by severity (error > warning > info)
    """
    issues = []

    for file in parsed_diff["files"]:
        file_path = file["path"]
        language = file["language"]
        additions = file["additions"]

        if language == "unknown":
            continue

        added_code = "\n".join(additions)

        if language == "python":
            # Always run error/warning checks
            issues.extend(check_bare_except(added_code, file_path))
            issues.extend(check_print_statements(added_code, file_path))
            issues.extend(run_ruff_check_sync(added_code, file_path))
            if include_info:
                issues.extend(check_missing_type_annotations(added_code, file_path))
                issues.extend(check_missing_docstrings(added_code, file_path))
                issues.extend(check_long_functions(added_code, file_path))
                issues.extend(check_unused_imports(added_code, file_path))
        elif language in ["javascript", "typescript"]:
            issues.extend(check_javascript_code(added_code, file_path))

        # Universal checks
        issues.extend(check_long_lines(added_code, file_path))
        issues.extend(check_trailing_whitespace(additions, file_path))
        issues.extend(check_todo_comments(added_code, file_path))

    # If no errors/warnings, show info-level issues so something is always useful
    has_real_issues = any(i.get("severity") in ("error", "warning") for i in issues)
    if not has_real_issues and not include_info:
        # Re-run with info enabled so the result isn't empty
        return run_static_checks(parsed_diff, include_info=True)

    # Filter out info if real issues exist (avoid noise burying errors)
    if has_real_issues and not include_info:
        issues = [i for i in issues if i.get("severity") != "info"]

    return issues


def check_python_code(code: str, file_path: str) -> List[Dict]:
    """
    Run Python-specific static checks
    
    Args:
        code: Python code to check
        file_path: Path to the file
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check for bare except clauses
    issues.extend(check_bare_except(code, file_path))
    
    # Check for print statements (not in test files)
    if "test" not in file_path.lower():
        issues.extend(check_print_statements(code, file_path))
    
    # Check for missing type annotations
    issues.extend(check_missing_type_annotations(code, file_path))
    
    # Check for unused imports (simple heuristic)
    issues.extend(check_unused_imports(code, file_path))
    
    # Check for missing docstrings
    issues.extend(check_missing_docstrings(code, file_path))
    
    # Check for long functions
    issues.extend(check_long_functions(code, file_path))
    
    return issues

async def run_ruff_check_async(code: str, file_path: str) -> List[Dict]:
    """Run ruff asynchronously using asyncio subprocess (non-blocking)."""
    issues = []
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        proc = await asyncio.create_subprocess_exec(
            "ruff", "check", tmp_path,
            "--output-format=json",
            "--select=E,W,F,I",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill()
            logger.warning(f"Ruff timed out for {file_path}")
            return issues

        if stdout:
            try:
                ruff_issues = json.loads(stdout.decode())
                for issue in ruff_issues:
                    issues.append({
                        "severity": "error" if issue.get("code", "").startswith("E") else "warning",
                        "file": file_path,
                        "line": str(issue.get("location", {}).get("row", 1)),
                        "issue": f"[ruff {issue.get('code')}] {issue.get('message')}",
                        "fix": issue.get("fix", {}).get("message", "See ruff documentation") if issue.get("fix") else "N/A",
                        "source": "static",
                        "category": "convention-violation"
                    })
            except json.JSONDecodeError:
                pass
    except FileNotFoundError:
        logger.debug("ruff not found in PATH — skipping ruff check")
    except Exception as e:
        logger.warning(f"Ruff check failed for {file_path}: {e}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return issues


def run_ruff_check_sync(code: str, file_path: str) -> List[Dict]:
    """Synchronous ruff wrapper that works inside run_in_executor thread context."""
    import subprocess
    issues = []
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        result = subprocess.run(
            ["ruff", "check", tmp_path, "--output-format=json", "--select=E,W,F,I"],
            capture_output=True, text=True, timeout=10
        )

        if result.stdout:
            try:
                ruff_issues = json.loads(result.stdout)
                for issue in ruff_issues:
                    issues.append({
                        "severity": "error" if issue.get("code", "").startswith("E") else "warning",
                        "file": file_path,
                        "line": str(issue.get("location", {}).get("row", 1)),
                        "issue": f"[ruff {issue.get('code')}] {issue.get('message')}",
                        "fix": issue.get("fix", {}).get("message", "See ruff documentation") if issue.get("fix") else "N/A",
                        "source": "static",
                        "category": "convention-violation"
                    })
            except json.JSONDecodeError:
                pass
    except FileNotFoundError:
        logger.debug("ruff not found in PATH — skipping ruff check")
    except Exception as e:
        logger.warning(f"Ruff check (sync) failed for {file_path}: {e}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return issues


# Legacy alias kept for any direct callers
run_ruff_check = run_ruff_check_sync


def check_javascript_code(code: str, file_path: str) -> List[Dict]:
    """
    Run JavaScript/TypeScript-specific static checks
    
    Args:
        code: JavaScript/TypeScript code to check
        file_path: Path to the file
        
    Returns:
        List of issues found
    """
    issues = []
    
    # Check for console.log (not in test files)
    if "test" not in file_path.lower():
        issues.extend(check_console_log(code, file_path))
    
    # Check for var usage (should use let/const)
    issues.extend(check_var_usage(code, file_path))
    
    # Check for == instead of ===
    issues.extend(check_loose_equality(code, file_path))
    
    return issues


def check_bare_except(code: str, file_path: str) -> List[Dict]:
    """Check for bare except clauses in Python"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        # Match "except:" with optional whitespace
        if re.search(r'except\s*:', line):
            issues.append({
                "severity": "error",
                "file": file_path,
                "line": str(i),
                "issue": "Bare except clause detected - catches all exceptions including system exits",
                "fix": "Specify exception type (e.g., 'except Exception:' or specific exception)",
                "source": "static"
            })
    
    return issues


def check_print_statements(code: str, file_path: str) -> List[Dict]:
    """Check for print() statements in production code"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        # Match print() calls (not in comments)
        if re.search(r'\bprint\s*\(', line) and not line.strip().startswith("#"):
            issues.append({
                "severity": "warning",
                "file": file_path,
                "line": str(i),
                "issue": "print() statement found in production code",
                "fix": "Use logging module instead of print() for production code",
                "source": "static"
            })
    
    return issues


def check_missing_type_annotations(code: str, file_path: str) -> List[Dict]:
    """Check for functions without type annotations in Python"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        # Match function definitions without type hints
        # Simple heuristic: def func() without -> or : type
        if re.match(r'\s*def\s+\w+\s*\([^)]*\)\s*:', line):
            # Check if it has return type annotation
            if "->" not in line:
                # Skip __init__, __str__, etc.
                if not re.search(r'def\s+__\w+__', line):
                    issues.append({
                        "severity": "info",
                        "file": file_path,
                        "line": str(i),
                        "issue": "Function missing return type annotation",
                        "fix": "Add return type annotation (e.g., '-> None' or '-> str')",
                        "source": "static"
                    })
    
    return issues


def check_unused_imports(code: str, file_path: str) -> List[Dict]:
    """Check for potentially unused imports (simple heuristic)"""
    issues = []
    lines = code.split("\n")
    
    imports = []
    code_body = []
    
    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            imports.append(line)
        else:
            code_body.append(line)
    
    code_text = "\n".join(code_body)
    
    for i, import_line in enumerate(imports, 1):
        # Extract imported names
        if "import " in import_line:
            # Handle "import x" or "from x import y"
            match = re.search(r'import\s+([\w, ]+)', import_line)
            if match:
                names = [n.strip() for n in match.group(1).split(",")]
                for name in names:
                    # Remove "as" aliases
                    actual_name = name.split(" as ")[-1].strip()
                    # Check if name is used in code
                    if actual_name and not re.search(r'\b' + re.escape(actual_name) + r'\b', code_text):
                        issues.append({
                            "severity": "warning",
                            "file": file_path,
                            "line": str(i),
                            "issue": f"Import '{actual_name}' appears unused",
                            "fix": f"Remove unused import '{actual_name}'",
                            "source": "static"
                        })
    
    return issues


def check_missing_docstrings(code: str, file_path: str) -> List[Dict]:
    """Check for functions/classes without docstrings"""
    issues = []
    lines = code.split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for function or class definition
        if re.match(r'\s*(def|class)\s+\w+', line):
            # Check if next non-empty line is a docstring
            j = i + 1
            has_docstring = False
            
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line:
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                    break
                j += 1
            
            if not has_docstring:
                # Skip private methods and __init__
                if not re.search(r'(def\s+_\w+|def\s+__init__)', line):
                    issues.append({
                        "severity": "info",
                        "file": file_path,
                        "line": str(i + 1),
                        "issue": "Function/class missing docstring",
                        "fix": "Add docstring describing purpose, parameters, and return value",
                        "source": "static"
                    })
        
        i += 1
    
    return issues


def check_long_functions(code: str, file_path: str) -> List[Dict]:
    """Check for functions longer than 50 lines"""
    issues = []
    lines = code.split("\n")
    
    current_function = None
    function_start = 0
    indent_level = 0
    
    for i, line in enumerate(lines):
        # Detect function start
        match = re.match(r'\s*def\s+(\w+)', line)
        if match:
            # Save previous function if it was long
            if current_function and (i - function_start) > 50:
                issues.append({
                    "severity": "info",
                    "file": file_path,
                    "line": str(function_start + 1),
                    "issue": f"Function '{current_function}' is {i - function_start} lines long (>50 lines)",
                    "fix": "Consider breaking into smaller functions",
                    "source": "static"
                })
            
            # Start tracking new function
            current_function = match.group(1)
            function_start = i
            indent_level = len(line) - len(line.lstrip())
    
    # Check last function
    if current_function and (len(lines) - function_start) > 50:
        issues.append({
            "severity": "info",
            "file": file_path,
            "line": str(function_start + 1),
            "issue": f"Function '{current_function}' is {len(lines) - function_start} lines long (>50 lines)",
            "fix": "Consider breaking into smaller functions",
            "source": "static"
        })
    
    return issues


def check_console_log(code: str, file_path: str) -> List[Dict]:
    """Check for console.log in JavaScript/TypeScript"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        if re.search(r'\bconsole\.log\s*\(', line) and not line.strip().startswith("//"):
            issues.append({
                "severity": "warning",
                "file": file_path,
                "line": str(i),
                "issue": "console.log() found in production code",
                "fix": "Remove console.log() or use proper logging library",
                "source": "static"
            })
    
    return issues


def check_var_usage(code: str, file_path: str) -> List[Dict]:
    """Check for var usage in JavaScript (should use let/const)"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        if re.search(r'\bvar\s+\w+', line) and not line.strip().startswith("//"):
            issues.append({
                "severity": "warning",
                "file": file_path,
                "line": str(i),
                "issue": "Using 'var' keyword (ES5 style)",
                "fix": "Use 'let' or 'const' instead of 'var' (ES6+)",
                "source": "static"
            })
    
    return issues


def check_loose_equality(code: str, file_path: str) -> List[Dict]:
    """Check for == instead of === in JavaScript"""
    issues = []
    lines = code.split("\n")

    for i, line in enumerate(lines, 1):
        if re.search(r'[^=!<>]==[^=]', line) and not line.strip().startswith("//"):
            issues.append({
                "severity": "warning",
                "file": file_path,
                "line": str(i),
                "issue": "Using loose equality (==) instead of strict equality (===)",
                "fix": "Use '===' for strict equality comparison",
                "source": "static"
            })

    return issues


def check_long_lines(code: str, file_path: str) -> List[Dict]:
    """Check for lines longer than 120 characters"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            issues.append({
                "severity": "info",
                "file": file_path,
                "line": str(i),
                "issue": f"Line is {len(line)} characters long (>120)",
                "fix": "Break long line into multiple lines",
                "source": "static"
            })
    
    return issues


def check_trailing_whitespace(lines: List[str], file_path: str) -> List[Dict]:
    """Check for trailing whitespace"""
    issues = []
    
    for i, line in enumerate(lines, 1):
        if line.endswith(" ") or line.endswith("\t"):
            issues.append({
                "severity": "info",
                "file": file_path,
                "line": str(i),
                "issue": "Line has trailing whitespace",
                "fix": "Remove trailing whitespace",
                "source": "static"
            })
    
    return issues


def check_todo_comments(code: str, file_path: str) -> List[Dict]:
    """Check for TODO/FIXME comments"""
    issues = []
    lines = code.split("\n")
    
    for i, line in enumerate(lines, 1):
        if re.search(r'(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
            issues.append({
                "severity": "info",
                "file": file_path,
                "line": str(i),
                "issue": "TODO/FIXME comment found",
                "fix": "Address TODO comment before merging or create a tracking issue",
                "source": "static"
            })
    
    return issues


# Made with Bob