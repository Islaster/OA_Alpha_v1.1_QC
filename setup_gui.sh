#!/bin/bash
#
# Setup script for OA GUI - Mac/Linux
# Creates a virtual environment and installs PySide6
#

echo "========================================"
echo "OA - Orientation Automator GUI Setup"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check for Python 3
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.8 or later."
    echo ""
    echo "Mac: brew install python3"
    echo "Ubuntu: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

echo "Using Python: $PYTHON"
$PYTHON --version
echo ""

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to create virtual environment!"
        echo "Make sure python3-venv is installed:"
        echo "  Ubuntu: sudo apt install python3-venv"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install PySide6
echo ""
echo "Installing PySide6..."
pip install PySide6

if [[ $? -eq 0 ]]; then
    echo ""
    echo "========================================"
    echo "✓ Setup complete!"
    echo "========================================"
    echo ""
    echo "To run the GUI:"
    echo "  ./run_gui.sh"
    echo ""
    echo "Or manually:"
    echo "  source venv/bin/activate"
    echo "  python gui.py"
    echo ""
else
    echo ""
    echo "ERROR: Failed to install PySide6"
    exit 1
fi

