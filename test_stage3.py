"""
Test script for Stage 3 LangGraph agent
"""

import os
import json
from stage3.pipeline import run_stage3

def test_stage3_agent():
    """Test the Stage 3 agent with a sample repository"""
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return False
    
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️  GITHUB_TOKEN not set (optional but recommended)")
    
    print("✅ Environment variables configured")
    
    # Test with a simple repository
    repo_url = "https://github.com/Tracer-Cloud/opensre"
    change_description = "Decouple node config typing from LangChain"
    
    print(f"\n🔍 Testing Stage 3 agent...")
    print(f"Repository: {repo_url}")
    print(f"Change: {change_description}")
    print("\n" + "="*60)
    
    try:
        result = run_stage3(repo_url, change_description)
        
        print("\n✅ Agent execution completed!")
        print("\n📊 Results:")
        print(json.dumps(result, indent=2))
        
        # Validate output structure
        required_fields = [
            "repo", "change_description", "files_affected", 
            "services_at_risk", "tests_to_update", "findings", "suggested_order"
        ]
        
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            print(f"\n⚠️  Missing fields: {missing_fields}")
            return False
        
        print("\n✅ All required fields present")
        
        # Check findings structure
        if result.get("findings"):
            print(f"\n📋 Found {len(result['findings'])} findings:")
            for i, finding in enumerate(result["findings"], 1):
                print(f"  {i}. {finding.get('finding', 'N/A')}")
                print(f"     Confidence: {finding.get('confidence', 0):.2f}")
                print(f"     Type: {finding.get('type', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("Stage 3 LangGraph Agent Test")
    print("="*60)
    
    success = test_stage3_agent()
    
    print("\n" + "="*60)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed")
    print("="*60)

# Made with Bob
