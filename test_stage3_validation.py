"""
Enhanced test script for Stage 3 with ground truth validation
Tests the full pipeline and computes accuracy metrics
"""

import os
import json
from stage3.pipeline import run_stage3
from stage3.ground_truth_pr1395 import (
    GROUND_TRUTH_PR1395,
    validate_stage3_output
)


def test_stage3_with_validation():
    """Test Stage 3 pipeline with ground truth validation"""
    
    print("="*70)
    print("Stage 3 Change Impact Analysis - Validation Test")
    print("="*70)
    
    # Check environment variables
    print("\n📋 Environment Check:")
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    print("✅ OPENAI_API_KEY configured")
    
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️  GITHUB_TOKEN not set (optional but recommended for rate limits)")
    else:
        print("✅ GITHUB_TOKEN configured")
    
    # Test configuration matching PR #1395
    repo_url = "https://github.com/Tracer-Cloud/opensre"
    change_description = GROUND_TRUTH_PR1395["description"]
    
    print(f"\n🎯 Test Configuration:")
    print(f"Repository: {repo_url}")
    print(f"PR #: {GROUND_TRUTH_PR1395['pr_number']}")
    print(f"Change: {change_description}")
    print(f"Expected files: {len(GROUND_TRUTH_PR1395['files_changed'])}")
    
    print("\n" + "="*70)
    print("🚀 Running Stage 3 Pipeline...")
    print("="*70)
    
    try:
        # Run the pipeline
        result = run_stage3(repo_url, change_description)
        
        print("\n✅ Pipeline execution completed!")
        
        # Display raw results
        print("\n📊 Raw Pipeline Output:")
        print("-"*70)
        print(json.dumps(result, indent=2))
        print("-"*70)
        
        # Validate against ground truth
        print("\n🔍 Validating Against Ground Truth (PR #1395)...")
        print("="*70)
        
        validation = validate_stage3_output(result)
        
        # Display file metrics
        print("\n📈 File Detection Metrics:")
        metrics = validation["file_metrics"]
        print(f"  Precision: {metrics['precision']:.1%} ({metrics['total_predicted']} predicted)")
        print(f"  Recall:    {metrics['recall']:.1%} ({metrics['total_actual']} actual)")
        print(f"  F1 Score:  {metrics['f1_score']:.1%}")
        print(f"  Summary:   {metrics['summary']}")
        
        if metrics['true_positives']:
            print(f"\n  ✅ Correctly Identified ({len(metrics['true_positives'])}):")
            for f in metrics['true_positives']:
                print(f"     • {f}")
        
        if metrics['false_negatives']:
            print(f"\n  ❌ Missed Files ({len(metrics['false_negatives'])}):")
            for f in metrics['false_negatives']:
                print(f"     • {f}")
        
        if metrics['false_positives']:
            print(f"\n  ⚠️  Extra Files ({len(metrics['false_positives'])}):")
            for f in metrics['false_positives']:
                print(f"     • {f}")
        
        # Display service detection (if available)
        if "service_detection" in validation:
            print("\n🎯 Service Detection:")
            svc = validation["service_detection"]
            print(f"  Coverage: {svc['coverage']:.1%}")
            if svc['overlap']:
                print(f"  Identified: {', '.join(svc['overlap'])}")
        
        # Display test detection
        print("\n🧪 Test File Detection:")
        test = validation["test_detection"]
        print(f"  Coverage: {test['coverage']:.1%}")
        if test['overlap']:
            print(f"  Identified: {', '.join(test['overlap'])}")
        
        # Display recommendations
        print("\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  {rec}")
        
        # Overall quality
        print("\n" + "="*70)
        quality = validation["overall_quality"]
        if quality == "PASS":
            print("✅ VALIDATION PASSED - Ready for demo!")
        else:
            print("⚠️  NEEDS IMPROVEMENT - Review recommendations above")
        print("="*70)
        
        # Save results
        output_file = "stage3_validation_results.json"
        with open(output_file, "w") as f:
            json.dump({
                "pipeline_output": result,
                "validation": validation
            }, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
        return validation["overall_quality"] == "PASS"
        
    except Exception as e:
        print(f"\n❌ Error during pipeline execution:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stage3_basic():
    """Basic test without validation (for quick checks)"""
    
    print("="*70)
    print("Stage 3 Basic Test (No Validation)")
    print("="*70)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return False
    
    repo_url = "https://github.com/Tracer-Cloud/opensre"
    change_description = "Decouple node config typing from LangChain"
    
    print(f"\nRepository: {repo_url}")
    print(f"Change: {change_description}")
    print("\n🚀 Running pipeline...\n")
    
    try:
        result = run_stage3(repo_url, change_description)
        
        print("✅ Success!")
        print("\n📊 Results:")
        print(f"  Files affected: {len(result.get('files_affected', []))}")
        print(f"  Services at risk: {len(result.get('services_at_risk', []))}")
        print(f"  Tests to update: {len(result.get('tests_to_update', []))}")
        print(f"  Findings: {len(result.get('findings', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--basic":
        success = test_stage3_basic()
    else:
        success = test_stage3_with_validation()
    
    print("\n" + "="*70)
    if success:
        print("✅ TEST PASSED")
        sys.exit(0)
    else:
        print("❌ TEST FAILED")
        sys.exit(1)

# Made with Bob
