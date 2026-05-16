#!/bin/bash

# Stage 3 Setup Script
# Sets up the LangGraph agent environment

echo "================================================"
echo "Stage 3: Change Impact Analysis - Setup"
echo "================================================"

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
echo ""
echo "Checking environment variables..."

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set"
    echo "   Set it with: export OPENAI_API_KEY='your-key'"
else
    echo "✅ OPENAI_API_KEY is set"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set (optional but recommended)"
    echo "   Set it with: export GITHUB_TOKEN='your-token'"
else
    echo "✅ GITHUB_TOKEN is set"
fi

echo ""
echo "================================================"
echo "Setup complete!"
echo ""
echo "To test the agent:"
echo "  python test_stage3.py"
echo ""
echo "To start the FastAPI server:"
echo "  uvicorn main:app --reload"
echo "================================================"

# Made with Bob
