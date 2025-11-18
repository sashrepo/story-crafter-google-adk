#!/bin/bash

echo "🎨 Story Crafter ADK Setup Script"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed!"
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv found"
echo ""

# Sync dependencies
echo "📦 Installing dependencies..."
uv sync

echo ""
echo "✅ Dependencies installed!"
echo ""

# Check for API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  WARNING: GOOGLE_API_KEY not set!"
    echo ""
    echo "To set your API key, run:"
    echo "  export GOOGLE_API_KEY='your-key-here'"
    echo ""
    echo "Or create a .env file:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your key"
    echo ""
else
    echo "✅ GOOGLE_API_KEY found"
    echo ""
fi

echo "🎉 Setup Complete!"
echo ""
echo "Next steps:"
echo "  1. Set your API key (if not already set)"
echo "  2. Run the example: uv run python example.py"
echo "  3. Or use ADK CLI: uv run adk run agents/orchestrator/story_orchestrator"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Full documentation"
echo "  - QUICKSTART.md - Quick start guide"
echo "  - PROJECT_SUMMARY.md - Project overview"
echo ""
