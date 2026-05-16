#!/bin/bash

# Quick test script for enhanced pipeline
# Run this to test the improvements

echo "========================================"
echo "Enhanced Pipeline Test Script"
echo "========================================"
echo ""

# Check for API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY not set"
    echo "   export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  WARNING: GITHUB_TOKEN not set"
    echo "   GitHub search will be rate-limited"
    echo "   export GITHUB_TOKEN='your-token-here'"
    echo ""
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q requests langchain-openai langgraph 2>/dev/null

# Run the test
echo ""
echo "🚀 Running enhanced pipeline test..."
echo ""

cd "$(dirname "$0")"
python test_enhanced_pipeline.py

echo ""
echo "✅ Test complete!"
echo ""
echo "📄 Results saved to:"
echo "   - enhanced_pipeline_result.json"
echo "   - enhanced_validation_results.json"

# Made with Bob
