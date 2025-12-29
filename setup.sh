#!/bin/bash
#
# Setup script for Bounding Box Optimizer - Mac/Linux
# Auto-detects Blender or prompts for path
#

echo "========================================"
echo "Bounding Box Optimizer - Setup"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER_PATH_FILE="$SCRIPT_DIR/blender_path.txt"

# Function to find Blender
find_blender() {
    # Check if we have a saved path
    if [[ -f "$BLENDER_PATH_FILE" ]]; then
        local saved_path=$(cat "$BLENDER_PATH_FILE")
        if [[ -x "$saved_path" ]]; then
            echo "$saved_path"
            return 0
        fi
    fi
    
    # Check environment variable first
    if [[ -n "$BLENDER" && -x "$BLENDER" ]]; then
        echo "$BLENDER"
        return 0
    fi
    
    # Detect OS
    local os_type=""
    case "$(uname -s)" in
        Darwin*)  os_type="mac" ;;
        Linux*)   os_type="linux" ;;
        *)        os_type="unknown" ;;
    esac
    
    # Mac locations
    if [[ "$os_type" == "mac" ]]; then
        # Check Applications folder (all Blender versions)
        for version in 4.5 4.4 4.3 4.2 4.1 4.0 3.6 3.5 3.4 3.3; do
            local app_path="/Applications/Blender.app/Contents/MacOS/Blender"
            if [[ -x "$app_path" ]]; then
                echo "$app_path"
                return 0
            fi
        done
        
        # Check user Applications
        if [[ -x "$HOME/Applications/Blender.app/Contents/MacOS/Blender" ]]; then
            echo "$HOME/Applications/Blender.app/Contents/MacOS/Blender"
            return 0
        fi
        
        # Check Homebrew
        if [[ -x "/opt/homebrew/bin/blender" ]]; then
            echo "/opt/homebrew/bin/blender"
            return 0
        fi
        if [[ -x "/usr/local/bin/blender" ]]; then
            echo "/usr/local/bin/blender"
            return 0
        fi
    fi
    
    # Linux locations
    if [[ "$os_type" == "linux" ]]; then
        # Standard package manager installs
        if [[ -x "/usr/bin/blender" ]]; then
            echo "/usr/bin/blender"
            return 0
        fi
        
        # Snap installation
        if [[ -x "/snap/bin/blender" ]]; then
            echo "/snap/bin/blender"
            return 0
        fi
        
        # Flatpak (check if command exists)
        if command -v flatpak &> /dev/null; then
            if flatpak list | grep -q "org.blender.Blender"; then
                echo "flatpak run org.blender.Blender"
                return 0
            fi
        fi
        
        # Local installs
        if [[ -x "/usr/local/bin/blender" ]]; then
            echo "/usr/local/bin/blender"
            return 0
        fi
        
        # Home directory installs
        for version in 4.5 4.4 4.3 4.2 4.1 4.0 3.6; do
            if [[ -x "$HOME/blender-$version/blender" ]]; then
                echo "$HOME/blender-$version/blender"
                return 0
            fi
        done
        
        if [[ -x "$HOME/blender/blender" ]]; then
            echo "$HOME/blender/blender"
            return 0
        fi
        
        # Steam installation
        local steam_path="$HOME/.steam/steam/steamapps/common/Blender/blender"
        if [[ -x "$steam_path" ]]; then
            echo "$steam_path"
            return 0
        fi
    fi
    
    # Try PATH as last resort
    if command -v blender &> /dev/null; then
        which blender
        return 0
    fi
    
    return 1
}

# Try to find Blender
echo "Searching for Blender installation..."
BLENDER=$(find_blender)

if [[ -z "$BLENDER" ]]; then
    echo ""
    echo "========================================"
    echo "Blender not found automatically!"
    echo "========================================"
    echo ""
    
    # Show OS-specific hints
    case "$(uname -s)" in
        Darwin*)
            echo "Common Mac locations:"
            echo "  /Applications/Blender.app/Contents/MacOS/Blender"
            echo ""
            echo "Install with: brew install --cask blender"
            ;;
        Linux*)
            echo "Common Linux locations:"
            echo "  /usr/bin/blender"
            echo "  /snap/bin/blender"
            echo "  ~/blender-4.2/blender"
            echo ""
            echo "Install with:"
            echo "  Ubuntu/Debian: sudo apt install blender"
            echo "  Snap: sudo snap install blender --classic"
            ;;
    esac
    
    echo ""
    echo "Please enter the full path to Blender executable:"
    echo "(You can drag-drop the file into terminal on Mac)"
    echo ""
    read -p "Blender path: " BLENDER
    
    # Remove quotes if user included them
    BLENDER="${BLENDER%\"}"
    BLENDER="${BLENDER#\"}"
    BLENDER="${BLENDER%\'}"
    BLENDER="${BLENDER#\'}"
    
    # Validate
    if [[ ! -x "$BLENDER" ]]; then
        echo ""
        echo "ERROR: Not a valid executable: $BLENDER"
        echo "Please check the path and try again."
        exit 1
    fi
fi

echo ""
echo "Found Blender: $BLENDER"
echo ""

# Save path for future use
echo "$BLENDER" > "$BLENDER_PATH_FILE"
echo "Path saved to: $BLENDER_PATH_FILE"
echo ""

# Create Python script to install dependencies
cat > "$SCRIPT_DIR/_install_deps.py" << 'PYTHON_SCRIPT'
import subprocess
import sys

print("Installing dependencies into Blender's Python...")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print("")

packages = ["scipy", "numpy"]

for package in packages:
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(f"  ✓ {package} installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Failed to install {package}: {e}")
    except Exception as e:
        print(f"  ⚠ Error installing {package}: {e}")

print("")
print("Setup complete!")
PYTHON_SCRIPT

# Run the install script through Blender
echo "Installing dependencies into Blender's Python..."
echo ""

# Handle flatpak specially
if [[ "$BLENDER" == "flatpak run"* ]]; then
    $BLENDER --background --python "$SCRIPT_DIR/_install_deps.py"
else
    "$BLENDER" --background --python "$SCRIPT_DIR/_install_deps.py"
fi

# Clean up
rm -f "$SCRIPT_DIR/_install_deps.py"

echo ""
echo "========================================"
echo "✓ Setup complete!"
echo "========================================"
echo ""
echo "You can now run:"
echo "  ./run_optimizer.sh input_file.obj  (command line)"
echo "  ./run_gui.sh                       (GUI mode)"
echo ""
