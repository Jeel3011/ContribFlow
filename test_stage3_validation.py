import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_enhanced_pipeline():
    """Test the enhanced pipeline against PR #1395"""
    from stage3.enhanced_pipeline import run_enhanced_pipeline
    from stage3.ground_truth_pr1395 import (
        GROUND_TRUTH_PR1395,
        validate_stage3_output
    )
    
    print("Testing Enhanced Pipeline for Stage 3...")
    
    result = run_enhanced_pipeline(
        repo_url="https://github.com/Tracer-Cloud/opensre",
        change_description=GROUND_TRUTH_PR1395["description"]
    )
    
    validation = validate_stage3_output(result)
    
    print("\n" + "="*60)
    print("ENHANCED PIPELINE VALIDATION RESULTS")
    print("="*60)
    print(f"Precision: {validation['file_metrics']['precision']}")
    print(f"Recall: {validation['file_metrics']['recall']}")
    print(f"F1 Score: {validation['file_metrics']['f1_score']}")
    print(f"Quality: {validation['overall_quality']}")
    
    for rec in validation["recommendations"]:
        print(rec)
        
    # Output metrics
    print("\nDetailed Output Metrics:")
    print(json.dumps(validation['file_metrics'], indent=2))
    
    return validation

if __name__ == "__main__":
    test_enhanced_pipeline()
