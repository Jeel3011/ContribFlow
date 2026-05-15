"""
Tests for Stage 3: Change Impact Analysis
"""

import os
import tempfile
from pathlib import Path
import pytest
from change_impact import analyze_change_impact


def create_test_repo():
    """
    Create a temporary test repository with sample Python files.
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Create main module
    utils_dir = repo_path / "utils"
    utils_dir.mkdir()
    
    (utils_dir / "__init__.py").write_text("")
    (utils_dir / "helper.py").write_text("""
def calculate(x, y):
    return x + y
""")
    
    # Create file that imports helper
    (repo_path / "main.py").write_text("""
from utils.helper import calculate

def main():
    result = calculate(1, 2)
    print(result)
""")
    
    # Create another dependent file
    (repo_path / "processor.py").write_text("""
import utils.helper

def process():
    return utils.helper.calculate(5, 10)
""")
    
    # Create test file
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_helper.py").write_text("""
from utils.helper import calculate

def test_calculate():
    assert calculate(2, 3) == 5
""")
    
    # Create independent file
    (repo_path / "independent.py").write_text("""
def standalone():
    return "I don't import helper"
""")
    
    return str(repo_path)


def test_analyze_change_impact_with_dependents():
    """
    Test that analyze_change_impact correctly identifies dependent files.
    """
    repo_path = create_test_repo()
    
    try:
        result = analyze_change_impact(repo_path, "utils/helper.py")
        
        assert result["target"] == "utils/helper.py"
        assert len(result["dependent_files"]) == 3  # main.py, processor.py, test_helper.py
        assert len(result["affected_tests"]) == 1  # test_helper.py
        assert result["risk_level"] == "medium"  # 1-3 dependents
        
        # Check that dependent files are in the list
        dependent_names = [Path(f).name for f in result["dependent_files"]]
        assert "main.py" in dependent_names
        assert "processor.py" in dependent_names
        assert "test_helper.py" in dependent_names
        
        # Check that test file is identified
        test_names = [Path(f).name for f in result["affected_tests"]]
        assert "test_helper.py" in test_names
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(repo_path)


def test_analyze_change_impact_no_dependents():
    """
    Test that analyze_change_impact returns low risk for files with no dependents.
    """
    repo_path = create_test_repo()
    
    try:
        result = analyze_change_impact(repo_path, "independent.py")
        
        assert result["target"] == "independent.py"
        assert len(result["dependent_files"]) == 0
        assert len(result["affected_tests"]) == 0
        assert result["risk_level"] == "low"
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(repo_path)


def test_analyze_change_impact_medium_risk():
    """
    Test medium risk level (1-3 dependents).
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    try:
        # Create a module with exactly 2 dependents
        (repo_path / "module.py").write_text("""
def func():
    pass
""")
        
        (repo_path / "user1.py").write_text("""
from module import func
""")
        
        (repo_path / "user2.py").write_text("""
import module
""")
        
        result = analyze_change_impact(str(repo_path), "module.py")
        
        assert result["target"] == "module.py"
        assert len(result["dependent_files"]) == 2
        assert result["risk_level"] == "medium"
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(str(repo_path))


if __name__ == "__main__":
    # Run tests
    print("Running test_analyze_change_impact_with_dependents...")
    test_analyze_change_impact_with_dependents()
    print("✓ Passed")
    
    print("Running test_analyze_change_impact_no_dependents...")
    test_analyze_change_impact_no_dependents()
    print("✓ Passed")
    
    print("Running test_analyze_change_impact_medium_risk...")
    test_analyze_change_impact_medium_risk()
    print("✓ Passed")
    
    print("\nAll tests passed!")

# Made with Bob
