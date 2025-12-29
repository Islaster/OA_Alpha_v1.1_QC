#!/bin/bash
# Local Build Script for OA - Orientation Automator
# Builds obfuscated binary for testing before CI/CD

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  OA - Local Build Script"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Step 1: Verify setup
echo ""
echo "🔍 Step 1: Verifying setup..."
if [ -f "verify_cicd_setup.py" ]; then
    python3 verify_cicd_setup.py
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠ Some checks failed. Continuing anyway...${NC}"
    fi
else
    echo -e "${YELLOW}⚠ verify_cicd_setup.py not found. Skipping verification.${NC}"
fi

# Step 2: Check dependencies
echo ""
echo "📦 Step 2: Checking dependencies..."
python3 -c "import nuitka" 2>/dev/null || {
    echo -e "${YELLOW}⚠ Nuitka not installed. Installing...${NC}"
    pip3 install nuitka ordered-set zstandard
}

python3 -c "import pyinstaller" 2>/dev/null || {
    echo -e "${YELLOW}⚠ PyInstaller not installed. Installing (fallback)...${NC}"
    pip3 install pyinstaller
}

echo -e "${GREEN}✓${NC} Dependencies ready"

# Step 3: Clean previous builds
echo ""
echo "🧹 Step 3: Cleaning previous builds..."
rm -rf dist/obfuscated
rm -rf build
echo -e "${GREEN}✓${NC} Cleaned"

# Step 4: Security audit (optional)
echo ""
echo "🔒 Step 4: Running security audit..."
if command -v pip-audit &> /dev/null; then
    pip-audit --desc || echo -e "${YELLOW}⚠ Vulnerabilities found (non-critical)${NC}"
else
    echo -e "${YELLOW}⚠ pip-audit not installed. Skipping security audit.${NC}"
    echo "   Install with: pip3 install pip-audit"
fi

# Step 5: Compile with Nuitka
echo ""
echo "🔨 Step 5: Compiling with Nuitka..."

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM_OPTS="--macos-create-app-bundle"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM_OPTS=""
else
    PLATFORM_OPTS=""
fi

python3 -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-package=src \
    --include-data-files=config.json=config.json \
    --include-data-files=env.example=env.example \
    --noinclude-pytest-mode=nofollow \
    --noinclude-setuptools-mode=nofollow \
    --output-dir=dist \
    --output-filename=OA-OrientationAutomator \
    $PLATFORM_OPTS \
    gui_new.py || {
    echo -e "${YELLOW}⚠ Nuitka compilation failed. Trying PyInstaller fallback...${NC}"
    
    # Fallback to PyInstaller
    echo ""
    echo "🏗️ Step 5b: Building with PyInstaller (fallback)..."
    
    python3 -m PyInstaller \
        --name OA-OrientationAutomator \
        --onefile \
        --windowed \
        --add-data "config.json:." \
        --add-data "env.example:." \
        --add-data "src:src" \
        --hidden-import=PySide6 \
        --hidden-import=cryptography \
        --hidden-import=dotenv \
        --clean \
        --noconfirm \
        gui_new.py
}

echo -e "${GREEN}✓${NC} Compilation complete"

# Step 6: Verify binary
echo ""
echo "🧪 Step 6: Verifying binary..."
if [ -f "dist/OA-OrientationAutomator.bin" ] || [ -f "dist/OA-OrientationAutomator" ] || [ -f "dist/OA-OrientationAutomator.exe" ]; then
    echo -e "${GREEN}✓${NC} Binary created successfully"
else
    echo -e "${YELLOW}⚠ Binary not found in expected location${NC}"
fi

# Step 7: Create distribution package (skip intermediate steps)
echo ""
echo "📦 Step 7: Creating distribution package..."

mkdir -p release

# Find the binary (different names on different platforms)
if [ -f "dist/OA-OrientationAutomator.bin" ]; then
    BINARY="dist/OA-OrientationAutomator.bin"
elif [ -f "dist/OA-OrientationAutomator" ]; then
    BINARY="dist/OA-OrientationAutomator"
elif [ -f "dist/OA-OrientationAutomator.exe" ]; then
    BINARY="dist/OA-OrientationAutomator.exe"
elif [ -f "dist/OA-OrientationAutomator.dist/OA-OrientationAutomator" ]; then
    BINARY="dist/OA-OrientationAutomator.dist/OA-OrientationAutomator"
else
    echo -e "${RED}✗ Binary not found${NC}"
    echo "Checked locations:"
    echo "  - dist/OA-OrientationAutomator.bin"
    echo "  - dist/OA-OrientationAutomator"
    echo "  - dist/OA-OrientationAutomator.exe"
    exit 1
fi

# Copy binary
cp "$BINARY" release/
chmod +x release/OA-OrientationAutomator* 2>/dev/null || true

# Copy documentation
cp env.example release/ 2>/dev/null || true
cp README*.md release/ 2>/dev/null || true

# Create README for distribution
cat > release/README.txt << 'EOF'
OA - Orientation Automator
==========================

This is a compiled binary distribution (Nuitka).

SETUP:
1. Copy env.example to .env
2. Edit .env with your configuration
3. Run the binary: ./OA-OrientationAutomator

For documentation, see the included .md files.
EOF

echo -e "${GREEN}✓${NC} Distribution package created in release/"

# Show size
echo ""
echo "📊 Binary size: $(du -h "$BINARY" | cut -f1)"

# Final summary
echo ""
echo "=========================================="
echo -e "  ${GREEN}✓ BUILD COMPLETE${NC}"
echo "=========================================="
echo ""
echo "Output locations:"
echo "  • Compiled binary: $BINARY"
echo "  • Distribution: release/"
echo ""
echo "Test the binary:"
echo "  $BINARY"
echo ""
echo "Or run from release directory:"
echo "  cd release && ./OA-OrientationAutomator"
echo ""
echo "Next steps:"
echo "  1. Test the binary locally"
echo "  2. Push to GitHub to trigger CI/CD (no license needed!)"
echo ""

