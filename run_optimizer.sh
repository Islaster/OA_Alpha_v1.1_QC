#!/bin/bash
#
# Bounding Box Optimizer - Mac/Linux Runner
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER_PATH_FILE="$SCRIPT_DIR/blender_path.txt"

# Check if input provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 input_file.obj [options]"
    echo ""
    echo "Options:"
    echo "  -o, --output FILE    Output file path"
    echo "  -c, --config FILE    Configuration file"
    echo "  --no-ground          Skip ground detection"
    echo "  --no-learning        Disable learning system"
    echo "  --type TYPE          Object type/category"
    echo "  --report FILE        Save report to JSON"
    echo "  --debug              Enable debug mode"
    echo ""
    echo "Run setup.sh first to configure Blender path!"
    exit 1
fi

# Function to find Blender
find_blender() {
    # Check saved path first
    if [[ -f "$BLENDER_PATH_FILE" ]]; then
        local saved_path=$(cat "$BLENDER_PATH_FILE")
        if [[ -x "$saved_path" ]]; then
            echo "$saved_path"
            return 0
        fi
    fi
    
    # Check environment variable
    if [[ -n "$BLENDER" && -x "$BLENDER" ]]; then
        echo "$BLENDER"
        return 0
    fi
    
    # Mac locations
    if [[ -x "/Applications/Blender.app/Contents/MacOS/Blender" ]]; then
        echo "/Applications/Blender.app/Contents/MacOS/Blender"
        return 0
    fi
    if [[ -x "$HOME/Applications/Blender.app/Contents/MacOS/Blender" ]]; then
        echo "$HOME/Applications/Blender.app/Contents/MacOS/Blender"
        return 0
    fi
    
    # Linux locations
    if [[ -x "/usr/bin/blender" ]]; then
        echo "/usr/bin/blender"
        return 0
    fi
    if [[ -x "/snap/bin/blender" ]]; then
        echo "/snap/bin/blender"
        return 0
    fi
    
    # Homebrew
    if [[ -x "/opt/homebrew/bin/blender" ]]; then
        echo "/opt/homebrew/bin/blender"
        return 0
    fi
    if [[ -x "/usr/local/bin/blender" ]]; then
        echo "/usr/local/bin/blender"
        return 0
    fi
    
    # PATH
    if command -v blender &> /dev/null; then
        which blender
        return 0
    fi
    
    return 1
}

# Find Blender
BLENDER=$(find_blender)

if [[ -z "$BLENDER" ]]; then
    echo "ERROR: Blender not found!"
    echo "Please run setup.sh first to configure Blender path."
    exit 1
fi

echo "Using Blender: $BLENDER"
echo ""

# Run the optimizer
"$BLENDER" --background --python "$SCRIPT_DIR/bounding_box_minimizer.py" -- "$@"

echo ""
echo "Done!"
