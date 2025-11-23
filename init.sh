#!/bin/bash

# AI Agent Insure - Initialization Script
# This script cleans the project and prepares all data from scratch
#
# Usage:
#   ./init.sh           - Run script (venv will be activated during execution only)
#   source init.sh      - Source script (venv will remain activated after completion)

# Detect if script is being sourced or executed
IS_SOURCED=false
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    IS_SOURCED=true
fi

# Only use 'set -e' when executed (not sourced), to avoid exiting parent shell
if [ "$IS_SOURCED" = false ]; then
    set -e  # Exit on error
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Function to exit/return appropriately based on how script was invoked
_exit_script() {
    local exit_code=${1:-0}
    if [ "$IS_SOURCED" = true ]; then
        return $exit_code
    else
        exit $exit_code
    fi
}

echo "=========================================="
echo "AI Agent Insure - Project Initialization"
echo "=========================================="
echo ""
if [ "$IS_SOURCED" = true ]; then
    echo "ℹ️  Note: Script is being sourced - venv will remain active after completion"
else
    echo "ℹ️  Note: Script is being executed - venv activation will be lost on exit"
fi
echo ""
echo "🚀 Starting initialization..."
echo ""

echo ""
echo "Step 1: Removing .venv folder..."
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "  ✓ .venv deleted"
else
    echo "  ⊘ .venv not found (skipping)"
fi

echo ""
echo "Step 2: Removing all __pycache__ folders..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "  ✓ All __pycache__ folders and .pyc files removed"

echo ""
echo "Step 3: Clearing agent/logs directory..."
if [ -d "agent/logs" ]; then
    rm -f agent/logs/*.log 2>/dev/null || true
    rm -f agent/logs/* 2>/dev/null || true
    echo "  ✓ agent/logs cleared"
else
    mkdir -p agent/logs
    echo "  ⊘ agent/logs directory created"
fi

echo ""
echo "Step 4: Removing insured-db/insureds.db..."
if [ -f "insured-db/insureds.db" ]; then
    rm -f insured-db/insureds.db
    echo "  ✓ insureds.db deleted"
else
    echo "  ⊘ insureds.db not found (skipping)"
fi

echo ""
echo "Step 5: Removing vector-store/chroma_db folder..."
if [ -d "vector-store/chroma_db" ]; then
    rm -rf vector-store/chroma_db
    echo "  ✓ chroma_db folder deleted"
else
    echo "  ⊘ chroma_db folder not found (skipping)"
fi

echo ""
echo "=========================================="
echo "Cleanup complete! Setting up environment..."
echo "=========================================="
echo ""


echo "Step 6: Creating virtual environment..."
if command -v uv &> /dev/null; then
    uv venv --python python3.12
    echo "  ✓ Virtual environment created with uv"
else
    echo "  ✗ Error: uv command not found. Please install uv first."
    echo "     Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    _exit_script 1
fi

echo ""
echo "Step 7: Activating virtual environment..."
source .venv/bin/activate
if [ $? -eq 0 ]; then
    echo "  ✓ Virtual environment activated"
else
    echo "  ✗ Error: Failed to activate virtual environment"
    _exit_script 1
fi

echo ""
echo "Step 8: Installing dependencies..."
uv pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "  ✓ Dependencies installed"
else
    echo "  ✗ Error: Failed to install dependencies"
    _exit_script 1
fi

echo ""
echo "=========================================="
echo "Environment ready! Running data preparation..."
echo "=========================================="
echo ""

# Run the data preparation script
python run_data_prep.py

echo ""
echo "=========================================="
echo "✓ Initialization complete!"
echo "=========================================="
echo "Next steps:"
echo ""
if [ "$IS_SOURCED" = false ]; then
    # Script was executed (not sourced), so venv won't be active after exit
    echo "  1. Activate the virtual environment:"
    echo "     source .venv/bin/activate"
    echo ""
    echo "  2. Run the application:"
    echo "     python agent/app.py"
    echo ""
    echo "  Note: To keep the venv activated after running this script,"
    echo "        use 'source init.sh' instead of './init.sh'"
else
    # Script was sourced, so venv is already active
    echo "  1. Virtual environment is already activated ✓"
    echo ""
    echo "  2. Run the application:"
    echo "     python agent/app.py"
    echo ""
fi

