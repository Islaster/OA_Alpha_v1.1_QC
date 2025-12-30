#!/bin/bash
#
# Run the OA GUI - Mac/Linux
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Virtual environment not found!"
    echo "Please run setup_gui.sh first:"
    echo "  ./setup_gui.sh"
    exit 1
fi

# Activate virtual environment and run GUI
source "$VENV_DIR/bin/activate"
python "$SCRIPT_DIR/gui_new.py"

