"""
Test the enhanced pipeline against PR #1395 ground truth
"""

import os
import json
import sys
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
from stage3.enhanced_pipeline import run_enhanced_pipeline
from stage3.ground_truth_pr1395 import (
    GROUND_TRUTH_PR1395,
    validate_stage3_output
)


def test_enhanced_pipeline():
    """Test the enhanced pipeline with GitHub search and reverse deps"""
    
    print("\n" + "="*70)
    print("TESTING ENHANCED PIPELINE WITH GITHUB SEARCH + REVERSE DEPS")
    print("="*70)
    
    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set")
        sys.exit(1)
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  WARNING: GITHUB_TOKEN not set - search may be rate limited")
    
    print(f"\n📋 Testing against PR #{GROUND_TRUTH_PR1395['pr_number']}")
    print(f"Title: {GROUND_TRUTH_PR1395['title']}")
    print(f"Actual files changed: {GROUND_TRUTH_PR1395['total_files']}")
    
    # Run enhanced pipeline
    print("\n🚀 Running enhanced pipeline...")
    print("   - Extracting intent and keywords")
    print("   - Searching GitHub code")
    print("   - Building reverse dependencies")
    print("   - Analyzing impact with LLM")
    print("   - Iterative refinement (if needed)")
    
    try:
        result = run_enhanced_pipeline(
            repo_url="https://github.com/Tracer-Cloud/opensre",
            change_description=GROUND_TRUTH_PR1395["description"]
        )
        
        print("\n✅ Pipeline completed successfully")
        
        # Save result
        with open("enhanced_pipeline_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("📄 Result saved to: enhanced_pipeline_result.json")
        
        # Validate against ground truth
        print("\n" + "="*70)
        print("VALIDATION AGAINST GROUND TRUTH")
        print("="*70)
        
        validation = validate_stage3_output(result)
        
        # Print metrics
        metrics = validation["file_metrics"]
        print(f"\n📊 File Detection Metrics:")
        print(f"   Precision: {metrics['precision']:.1%} ({metrics['precision']:.3f})")
        print(f"   Recall:    {metrics['recall']:.1%} ({metrics['recall']:.3f})")
        print(f"   F1 Score:  {metrics['f1_score']:.1%} ({metrics['f1_score']:.3f})")
        print(f"   Summary:   {metrics['summary']}")
        
        # Print comparison with old system
        print(f"\n📈 Improvement vs Old System:")
        old_precision, old_recall, old_f1 = 0.167, 0.062, 0.091
        print(f"   Precision: {old_precision:.1%} → {metrics['precision']:.1%} ({(metrics['precision']-old_precision)*100:+.1f}%)")
        print(f"   Recall:    {old_recall:.1%} → {metrics['recall']:.1%} ({(metrics['recall']-old_recall)*100:+.1f}%)")
        print(f"   F1 Score:  {old_f1:.1%} → {metrics['f1_score']:.1%} ({(metrics['f1_score']-old_f1)*100:+.1f}%)")
        
        # Print true positives
        if metrics["true_positives"]:
            print(f"\n✅ Correctly Identified ({len(metrics['true_positives'])} files):")
            for file in metrics["true_positives"][:10]:
                print(f"   ✓ {file}")
            if len(metrics["true_positives"]) > 10:
                print(f"   ... and {len(metrics['true_positives'])-10} more")
        
        # Print false positives
        if metrics["false_positives"]:
            print(f"\n❌ False Positives ({len(metrics['false_positives'])} files):")
            for file in metrics["false_positives"][:5]:
                print(f"   ✗ {file}")
            if len(metrics["false_positives"]) > 5:
                print(f"   ... and {len(metrics['false_positives'])-5} more")
        
        # Print false negatives
        if metrics["false_negatives"]:
            print(f"\n⚠️  Missed Files ({len(metrics['false_negatives'])} files):")
            for file in metrics["false_negatives"][:5]:
                print(f"   - {file}")
            if len(metrics["false_negatives"]) > 5:
                print(f"   ... and {len(metrics['false_negatives'])-5} more")
        
        # Print test detection
        test_metrics = validation["test_detection"]
        print(f"\n🧪 Test File Detection:")
        print(f"   Predicted: {len(test_metrics['predicted'])} files")
        print(f"   Actual:    {len(test_metrics['actual'])} files")
        print(f"   Overlap:   {len(test_metrics['overlap'])} files")
        print(f"   Coverage:  {test_metrics['coverage']:.1%}")
        
        # Print recommendations
        print(f"\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"   {rec}")
        
        # Overall quality
        quality = validation["overall_quality"]
        quality_emoji = "✅" if quality == "PASS" else "⚠️"
        print(f"\n{quality_emoji} Overall Quality: {quality}")
        
        # Check if we meet targets
        print(f"\n🎯 Target Achievement:")
        target_recall = 0.60
        target_precision = 0.50
        target_f1 = 0.55
        
        recall_met = "✅" if metrics["recall"] >= target_recall else "❌"
        precision_met = "✅" if metrics["precision"] >= target_precision else "❌"
        f1_met = "✅" if metrics["f1_score"] >= target_f1 else "❌"
        
        print(f"   {recall_met} Recall ≥ {target_recall:.0%}: {metrics['recall']:.1%}")
        print(f"   {precision_met} Precision ≥ {target_precision:.0%}: {metrics['precision']:.1%}")
        print(f"   {f1_met} F1 Score ≥ {target_f1:.0%}: {metrics['f1_score']:.1%}")
        
        # Save validation results
        validation_output = {
            "pipeline_output": result,
            "validation": validation,
            "comparison": {
                "old_system": {
                    "precision": old_precision,
                    "recall": old_recall,
                    "f1_score": old_f1
                },
                "new_system": {
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"]
                },
                "improvement": {
                    "precision": metrics["precision"] - old_precision,
                    "recall": metrics["recall"] - old_recall,
                    "f1_score": metrics["f1_score"] - old_f1
                }
            }
        }
        
        with open("enhanced_validation_results.json", "w") as f:
            json.dump(validation_output, f, indent=2)
        
        print(f"\n📄 Full validation saved to: enhanced_validation_results.json")
        
        # Final verdict
        print("\n" + "="*70)
        if metrics["recall"] >= target_recall and metrics["precision"] >= target_precision:
            print("🎉 SUCCESS! Enhanced pipeline meets all target metrics!")
        elif metrics["recall"] >= target_recall or metrics["precision"] >= target_precision:
            print("✅ PARTIAL SUCCESS! Some targets met, continue improving.")
        else:
            print("⚠️  NEEDS IMPROVEMENT! Targets not yet met.")
        print("="*70 + "\n")
        
        return validation
        
    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_enhanced_pipeline()

# Made with Bob
