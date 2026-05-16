"""
Ground truth data from Tracer-Cloud/opensre PR #1395
Fetched from GitHub API on 2026-05-16

This file contains the actual files changed in a real merged PR
to compute precision/recall metrics for our impact analysis.
"""

# Actual files changed in PR #1395
# Source: https://github.com/Tracer-Cloud/opensre/pull/1395/files
GROUND_TRUTH_PR1395 = {
    "pr_number": 1395,
    "title": "refactor(nodes): decouple node config typing from LangChain",
    "description": """Fixes #1364

#### Describe the changes you have made in this PR -

This PR decouples OpenSRE's core node signatures from LangChain's `RunnableConfig`. 
- Introduced an internal `NodeConfig` TypedDict in `app/types/config.py`.
- Replaced `RunnableConfig` imports and type hints in all core nodes and runners.
- Added a `get_configurable` helper to safely extract configuration dictionaries.
- Added a regression test in `tests/types/test_config.py` to prevent future coupling.

### Demo/Screenshot for""",
    "state": "closed",
    "merged": True,
    
    # All files that were modified in this PR
    "files_changed": [
        "app/nodes/adapt_window/node.py",
        "app/nodes/auth.py",
        "app/nodes/chat.py",
        "app/nodes/extract_alert/extract_node.py",
        "app/nodes/plan_actions/node.py",
        "app/nodes/publish_findings/node.py",
        "app/nodes/resolve_integrations/node.py",
        "app/nodes/root_cause_diagnosis/node.py",
        "app/pipeline/graph.py",
        "app/pipeline/runners.py",
        "app/types/__init__.py",
        "app/types/config.py",
        "tests/benchmarks/toolcall_model_benchmark/pipeline_benchmark.py",
        "tests/nodes/adapt_window/test_node.py",
        "tests/test_auth.py",
        "tests/types/test_config.py"
],
    
    # Source code files (excluding tests and docs)
    "source_files": [
        "app/nodes/adapt_window/node.py",
        "app/nodes/auth.py",
        "app/nodes/chat.py",
        "app/nodes/extract_alert/extract_node.py",
        "app/nodes/plan_actions/node.py",
        "app/nodes/publish_findings/node.py",
        "app/nodes/resolve_integrations/node.py",
        "app/nodes/root_cause_diagnosis/node.py",
        "app/pipeline/graph.py",
        "app/pipeline/runners.py",
        "app/types/__init__.py",
        "app/types/config.py"
],
    
    # Test files that were updated
    "tests_updated": [
        "tests/benchmarks/toolcall_model_benchmark/pipeline_benchmark.py",
        "tests/nodes/adapt_window/test_node.py",
        "tests/test_auth.py",
        "tests/types/test_config.py"
],
    
    # Documentation files
    "doc_files": [],
    
    # Statistics
    "total_files": 16,
    "additions": 136,
    "deletions": 49,
}


def compute_accuracy_metrics(predicted_output: dict) -> dict:
    """
    Compute precision, recall, and F1 score for Stage 3 predictions
    
    Args:
        predicted_output: Stage 3 JSON output with 'files_affected' field
        
    Returns:
        Dictionary with precision, recall, F1, and detailed breakdown
    """
    predicted_files = set(predicted_output.get("files_affected", []))
    actual_files = set(GROUND_TRUTH_PR1395["files_changed"])
    
    # Calculate set intersections
    true_positives = predicted_files & actual_files
    false_positives = predicted_files - actual_files
    false_negatives = actual_files - predicted_files
    
    # Compute metrics
    precision = len(true_positives) / len(predicted_files) if predicted_files else 0.0
    recall = len(true_positives) / len(actual_files) if actual_files else 0.0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1_score, 3),
        "true_positives": sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "total_predicted": len(predicted_files),
        "total_actual": len(actual_files),
        "passes_threshold": recall >= 0.6,  # Target: catch 60%+ of real changes
        "summary": f"Caught {len(true_positives)}/{len(actual_files)} actual changes"
    }


def validate_stage3_output(predicted_output: dict) -> dict:
    """
    Full validation of Stage 3 output against ground truth
    
    Args:
        predicted_output: Complete Stage 3 JSON output
        
    Returns:
        Validation report with metrics and recommendations
    """
    metrics = compute_accuracy_metrics(predicted_output)
    
    # Check if tests were identified
    predicted_tests = set(predicted_output.get("tests_to_update", []))
    actual_tests = set(GROUND_TRUTH_PR1395["tests_updated"])
    test_overlap = predicted_tests & actual_tests
    
    # Generate recommendations
    recommendations = []
    if metrics["recall"] < 0.6:
        recommendations.append("⚠️ Recall below 0.6 - increase file fetch limit or improve keyword matching")
    if metrics["precision"] < 0.5:
        recommendations.append("⚠️ Precision below 0.5 - too many false positives, refine dependency analysis")
    if len(test_overlap) == 0 and actual_tests:
        recommendations.append("⚠️ No test files identified - improve test file detection")
    
    if not recommendations:
        recommendations.append("✅ All metrics meet quality thresholds")
    
    return {
        "file_metrics": metrics,
        "test_detection": {
            "predicted": sorted(predicted_tests),
            "actual": sorted(actual_tests),
            "overlap": sorted(test_overlap),
            "coverage": len(test_overlap) / len(actual_tests) if actual_tests else 0.0
        },
        "recommendations": recommendations,
        "overall_quality": "PASS" if metrics["passes_threshold"] else "NEEDS_IMPROVEMENT"
    }


# Example usage
if __name__ == "__main__":
    import json
    
    print("Ground Truth Data for PR #1395")
    print("="*60)
    print(f"Title: {GROUND_TRUTH_PR1395['title']}")
    print(f"State: {GROUND_TRUTH_PR1395['state']}")
    print(f"Merged: {GROUND_TRUTH_PR1395['merged']}")
    print(f"Total Files: {GROUND_TRUTH_PR1395['total_files']}")
    print(f"Source Files: {len(GROUND_TRUTH_PR1395['source_files'])}")
    print(f"Test Files: {len(GROUND_TRUTH_PR1395['tests_updated'])}")
    print(f"Doc Files: {len(GROUND_TRUTH_PR1395['doc_files'])}")
    print("\nFiles Changed:")
    for f in GROUND_TRUTH_PR1395['files_changed']:
        print(f"  - {f}")
