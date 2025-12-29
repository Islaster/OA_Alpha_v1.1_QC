# Local Build Guide

## 🏗️ Building Locally (Before CI/CD)

This guide shows you how to test the build process locally before pushing to GitHub.

## 📋 Prerequisites

### 1. Python 3.10+
```bash
python3 --version
# Should show 3.10 or higher
```

### 2. Install Build Dependencies
```bash
# Install build tools
pip install -r requirements-build.txt

# Install runtime dependencies
pip install -r requirements.txt
pip install -r requirements-security.txt
```

### 3. PyArmor License (Optional)
```bash
# Trial mode works without license
# For commercial use, get license from: https://pyarmor.dashingsoft.com/

# If you have a license:
pyarmor reg your-license-file.txt
```

## 🔨 Build Steps

### Step 1: Verify Setup
```bash
# Run verification script
python3 verify_cicd_setup.py

# Should show all green checkmarks
```

### Step 2: Security Audit
```bash
# Check for vulnerabilities
pip-audit --desc

# Check dependencies
safety check
```

### Step 3: Obfuscate Code
```bash
# Create obfuscated distribution
pyarmor gen \
    --output dist/obfuscated \
    --recursive \
    --enable-bcc \
    --enable-jit \
    --private \
    --restrict \
    src/

# Copy entry points
cp gui_new.py dist/obfuscated/
cp main_processor.py dist/obfuscated/

# Copy configuration
cp config.json dist/obfuscated/
cp env.example dist/obfuscated/
```

### Step 4: Test Obfuscated Code
```bash
# Test that obfuscated code runs
cd dist/obfuscated
python3 gui_new.py
cd ../..
```

### Step 5: Build Binary (Option A - PyApp)
```bash
cd dist/obfuscated

# Build standalone binary
pyapp build \
    --python-version 3.12 \
    --output ../OA-OrientationAutomator \
    .

cd ../..

# Test binary
./dist/OA-OrientationAutomator
```

### Step 6: Build Binary (Option B - PyInstaller)
```bash
cd dist/obfuscated

# Create spec file (or use existing)
pyi-makespec gui_new.py \
    --name OA-OrientationAutomator \
    --onefile \
    --windowed \
    --add-data "config.json:." \
    --add-data "env.example:." \
    --add-data "src:src"

# Build
pyinstaller OA-OrientationAutomator.spec --clean

# Binary will be in dist/dist/OA-OrientationAutomator

cd ../..
```

## 🧪 Testing

### Test Obfuscated Code
```bash
# GUI test
cd dist/obfuscated
python3 gui_new.py
cd ../..

# CLI test (requires Blender)
blender --background --python dist/obfuscated/main_processor.py -- test.obj
```

### Test Binary
```bash
# Run the binary
./dist/OA-OrientationAutomator

# Should launch GUI without Python installed
```

### Test with Configuration
```bash
# Create .env file
cp env.example .env

# Edit .env (if needed)
nano .env

# Run with environment
./dist/OA-OrientationAutomator
```

## 📦 Platform-Specific Builds

### Windows
```powershell
# Install dependencies
pip install -r requirements-build.txt

# Obfuscate
pyarmor gen --output dist/obfuscated --recursive src/

# Build with PyInstaller
cd dist/obfuscated
pyinstaller gui_new.py --onefile --windowed --name OA-OrientationAutomator

# Binary: dist/dist/OA-OrientationAutomator.exe
```

### macOS
```bash
# Install dependencies
pip3 install -r requirements-build.txt

# Obfuscate
pyarmor gen --output dist/obfuscated --recursive src/

# Build with PyInstaller
cd dist/obfuscated
pyinstaller gui_new.py --onefile --windowed --name OA-OrientationAutomator

# Create .app bundle
# Binary: dist/dist/OA-OrientationAutomator

# Sign (optional, requires Apple Developer account)
codesign --force --sign "Developer ID Application: Your Name" \
    dist/dist/OA-OrientationAutomator
```

### Linux
```bash
# Install dependencies
pip3 install -r requirements-build.txt

# Obfuscate
pyarmor gen --output dist/obfuscated --recursive src/

# Build with PyInstaller
cd dist/obfuscated
pyinstaller gui_new.py --onefile --windowed --name OA-OrientationAutomator

# Binary: dist/dist/OA-OrientationAutomator

# Make executable
chmod +x dist/dist/OA-OrientationAutomator
```

## 🔍 Verification

### Check Binary Size
```bash
ls -lh dist/OA-OrientationAutomator*

# Should be 30-100MB depending on platform
```

### Check Dependencies
```bash
# macOS/Linux
ldd dist/OA-OrientationAutomator

# Should show minimal system libraries
```

### Verify Obfuscation
```bash
# Check that .pyc files are created (not .py)
find dist/obfuscated -name "*.py" -not -name "gui_new.py" -not -name "main_processor.py"

# Should only show entry points, not source files
```

### Test Security Features
```bash
# Verify .env is required
./dist/OA-OrientationAutomator
# Should not contain hardcoded secrets

# Verify encryption
python3 -c "from src.security.encryption import encrypt_data; print(encrypt_data('test'))"
# Should show encrypted output
```

## 🚨 Troubleshooting

### PyArmor Issues

**Error: "PyArmor license not found"**
```bash
# Use trial mode (automatic)
# Or register license:
pyarmor reg your-license.txt
```

**Error: "Module not obfuscated"**
```bash
# Check output directory
ls -la dist/obfuscated/src/

# Re-run with verbose
pyarmor gen --output dist/obfuscated --recursive --verbose src/
```

### PyInstaller Issues

**Error: "Module not found"**
```bash
# Add to hidden imports in spec file
hiddenimports=[
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'cryptography.fernet',
    'dotenv',
]
```

**Error: "Failed to execute script"**
```bash
# Run with console to see errors
pyinstaller gui_new.py --onefile --console

# Check output for missing modules
```

### Binary Doesn't Run

**macOS: "App is damaged"**
```bash
# Remove quarantine attribute
xattr -cr dist/OA-OrientationAutomator

# Or sign the app (recommended)
codesign --force --sign - dist/OA-OrientationAutomator
```

**Linux: "Permission denied"**
```bash
# Make executable
chmod +x dist/OA-OrientationAutomator
```

**Windows: "Missing DLL"**
```bash
# Ensure all dependencies are bundled
pyinstaller --onefile --windowed --collect-all PySide6 gui_new.py
```

## 🎯 Quick Build Script

Create `build_local.sh` (macOS/Linux) or `build_local.bat` (Windows):

```bash
#!/bin/bash
# build_local.sh

set -e

echo "🔍 Verifying setup..."
python3 verify_cicd_setup.py

echo "🔒 Running security audit..."
pip-audit --desc || echo "⚠️ Vulnerabilities found"

echo "📦 Obfuscating code..."
pyarmor gen --output dist/obfuscated --recursive --enable-bcc --enable-jit src/
cp gui_new.py main_processor.py config.json env.example dist/obfuscated/

echo "🏗️ Building binary..."
cd dist/obfuscated
pyinstaller gui_new.py --onefile --windowed --name OA-OrientationAutomator
cd ../..

echo "✅ Build complete!"
echo "Binary: dist/obfuscated/dist/OA-OrientationAutomator"
```

Make executable and run:
```bash
chmod +x build_local.sh
./build_local.sh
```

## 📊 Build Comparison

| Method | Build Time | Size | Pros | Cons |
|--------|-----------|------|------|------|
| PyApp | ~2 min | 50MB | Fast, modern | Experimental |
| PyInstaller | ~5 min | 80MB | Mature, reliable | Larger size |
| Manual | ~1 min | 10MB | Small | Requires Python |

## 🔐 Security Checklist

Before building:
- [ ] No `.env` file in source (only `.env.example`)
- [ ] No hardcoded API keys or secrets
- [ ] All sensitive config in `env.example` (not real values)
- [ ] `.gitignore` updated to exclude `.env` and logs
- [ ] Security modules in place (`src/security/`)

After building:
- [ ] Binary runs without errors
- [ ] No source code visible in binary
- [ ] Configuration loads from `.env`
- [ ] Error messages are generic (no stack traces to user)
- [ ] Logs contain sanitized information only

## 🚀 Ready for CI/CD

Once local build succeeds:
1. ✅ Commit all changes
2. ✅ Add `PYARMOR_LICENSE` to GitHub Secrets
3. ✅ Push to main branch
4. ✅ Monitor Actions tab for build progress

Your GitHub Actions workflow will replicate these steps automatically for all platforms!

## 📖 Next Steps

- **Test locally**: Follow this guide
- **Verify setup**: Run `verify_cicd_setup.py`
- **Push to GitHub**: Let CI/CD handle multi-platform builds
- **Download artifacts**: From Actions tab or Releases

---

**Questions?** Check the workflow logs for detailed build information.

