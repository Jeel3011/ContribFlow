"""
Fetch ground truth data from a real GitHub PR
This script fetches actual file changes from Tracer-Cloud/opensre PR #1395
"""

import os
import requests
import json
from typing import Optional


def fetch_pr_files(owner: str, repo: str, pr_number: int) -> Optional[dict]:
    """
    Fetch files changed in a PR from GitHub API
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        
    Returns:
        Dictionary with PR details and changed files
    """
    # GitHub API endpoints
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        # Fetch PR details
        print(f"Fetching PR #{pr_number} from {owner}/{repo}...")
        pr_response = requests.get(pr_url, headers=headers)
        
        if pr_response.status_code == 404:
            print(f"❌ PR #{pr_number} not found in {owner}/{repo}")
            return None
        
        if pr_response.status_code == 403:
            print("❌ GitHub rate limit hit. Set GITHUB_TOKEN environment variable.")
            return None
        
        pr_response.raise_for_status()
        pr_data = pr_response.json()
        
        # Fetch files changed
        print(f"Fetching changed files...")
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()
        
        # Extract relevant information
        files_changed = [f["filename"] for f in files_data]
        
        # Categorize files
        test_files = [f for f in files_changed if "test" in f.lower()]
        source_files = [f for f in files_changed if f not in test_files and not f.endswith(".md")]
        doc_files = [f for f in files_changed if f.endswith(".md")]
        
        result = {
            "pr_number": pr_number,
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body", "")[:500],  # First 500 chars
            "state": pr_data.get("state", ""),
            "merged": pr_data.get("merged", False),
            "files_changed": files_changed,
            "source_files": source_files,
            "test_files": test_files,
            "doc_files": doc_files,
            "total_files": len(files_changed),
            "additions": sum(f.get("additions", 0) for f in files_data),
            "deletions": sum(f.get("deletions", 0) for f in files_data),
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching PR data: {str(e)}")
        return None


def generate_ground_truth_file(pr_data: dict, output_file: str = "stage3/ground_truth_pr1395.py"):
    """
    Generate ground truth Python file from PR data
    
    Args:
        pr_data: Dictionary with PR information
        output_file: Path to output file
    """
    content = f'''"""
Ground truth data from Tracer-Cloud/opensre PR #{pr_data["pr_number"]}
Fetched from GitHub API on {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}

This file contains the actual files changed in a real merged PR
to compute precision/recall metrics for our impact analysis.
"""

# Actual files changed in PR #{pr_data["pr_number"]}
# Source: https://github.com/Tracer-Cloud/opensre/pull/{pr_data["pr_number"]}/files
GROUND_TRUTH_PR1395 = {{
    "pr_number": {pr_data["pr_number"]},
    "title": "{pr_data["title"]}",
    "description": """{pr_data["description"]}""",
    "state": "{pr_data["state"]}",
    "merged": {pr_data["merged"]},
    
    # All files that were modified in this PR
    "files_changed": {json.dumps(pr_data["files_changed"], indent=8)},
    
    # Source code files (excluding tests and docs)
    "source_files": {json.dumps(pr_data["source_files"], indent=8)},
    
    # Test files that were updated
    "tests_updated": {json.dumps(pr_data["test_files"], indent=8)},
    
    # Documentation files
    "doc_files": {json.dumps(pr_data["doc_files"], indent=8)},
    
    # Statistics
    "total_files": {pr_data["total_files"]},
    "additions": {pr_data["additions"]},
    "deletions": {pr_data["deletions"]},
}}


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
    
    return {{
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1_score, 3),
        "true_positives": sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "total_predicted": len(predicted_files),
        "total_actual": len(actual_files),
        "passes_threshold": recall >= 0.6,  # Target: catch 60%+ of real changes
        "summary": f"Caught {{len(true_positives)}}/{{len(actual_files)}} actual changes"
    }}


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
    
    return {{
        "file_metrics": metrics,
        "test_detection": {{
            "predicted": sorted(predicted_tests),
            "actual": sorted(actual_tests),
            "overlap": sorted(test_overlap),
            "coverage": len(test_overlap) / len(actual_tests) if actual_tests else 0.0
        }},
        "recommendations": recommendations,
        "overall_quality": "PASS" if metrics["passes_threshold"] else "NEEDS_IMPROVEMENT"
    }}


# Example usage
if __name__ == "__main__":
    import json
    
    print("Ground Truth Data for PR #{pr_data["pr_number"]}")
    print("="*60)
    print(f"Title: {{GROUND_TRUTH_PR1395['title']}}")
    print(f"State: {{GROUND_TRUTH_PR1395['state']}}")
    print(f"Merged: {{GROUND_TRUTH_PR1395['merged']}}")
    print(f"Total Files: {{GROUND_TRUTH_PR1395['total_files']}}")
    print(f"Source Files: {{len(GROUND_TRUTH_PR1395['source_files'])}}")
    print(f"Test Files: {{len(GROUND_TRUTH_PR1395['tests_updated'])}}")
    print(f"Doc Files: {{len(GROUND_TRUTH_PR1395['doc_files'])}}")
    print("\\nFiles Changed:")
    for f in GROUND_TRUTH_PR1395['files_changed']:
        print(f"  - {{f}}")
'''
    
    with open(output_file, "w") as f:
        f.write(content)
    
    print(f"✅ Ground truth file generated: {output_file}")


def main():
    """Main function to fetch and generate ground truth"""
    
    print("="*70)
    print("Ground Truth Data Fetcher for Stage 3 Validation")
    print("="*70)
    
    # Check for GitHub token
    if not os.getenv("GITHUB_TOKEN"):
        print("\n⚠️  GITHUB_TOKEN not set. You may hit rate limits.")
        print("   Set it with: export GITHUB_TOKEN='your-token'")
        print()
    
    # Fetch PR data from the actual repository
    # Using Tracer-Cloud/opensre PR #1395 as ground truth
    owner = "Tracer-Cloud"
    repo = "opensre"
    pr_number = 1395
    
    pr_data = fetch_pr_files(owner, repo, pr_number)
    
    if not pr_data:
        print("\n❌ Failed to fetch PR data. Using placeholder data instead.")
        print("   Please check:")
        print("   1. Repository exists: https://github.com/Tracer-Cloud/opensre")
        print("   2. PR #1395 exists")
        print("   3. GITHUB_TOKEN is set (if hitting rate limits)")
        return False
    
    # Display summary
    print(f"\n✅ Successfully fetched PR #{pr_number}")
    print(f"\nPR Details:")
    print(f"  Title: {pr_data['title']}")
    print(f"  State: {pr_data['state']}")
    print(f"  Merged: {pr_data['merged']}")
    print(f"  Total Files: {pr_data['total_files']}")
    print(f"  Additions: +{pr_data['additions']}")
    print(f"  Deletions: -{pr_data['deletions']}")
    
    print(f"\n📁 Files Changed ({pr_data['total_files']}):")
    for f in pr_data['files_changed']:
        print(f"  • {f}")
    
    # Generate ground truth file
    print(f"\n📝 Generating ground truth file...")
    generate_ground_truth_file(pr_data)
    
    print("\n" + "="*70)
    print("✅ Ground truth data ready for validation!")
    print("="*70)
    print("\nNext steps:")
    print("1. Review the generated file: stage3/ground_truth_pr1395.py")
    print("2. Run validation: python test_stage3_validation.py")
    
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

# Made with Bob
