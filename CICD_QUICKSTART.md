# CI/CD Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Add PyArmor License Secret (2 minutes)

```bash
# Go to GitHub:
# Repository → Settings → Secrets and variables → Actions
# Click "New repository secret"
# Name: PYARMOR_LICENSE
# Value: [paste your license]
```

**Don't have a license?** The pipeline will use trial mode automatically.

### 2. Push to GitHub (1 minute)

```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

### 3. Watch Build (2 minutes)

- Go to **Actions** tab
- Watch the build progress
- Download artifacts when complete

## 🎯 What Happens Automatically

```
Push to main
    ↓
Security Audit (30s)
    ├─ pip-audit (vulnerabilities)
    ├─ safety check (dependencies)
    └─ secret scanning (hardcoded keys)
    ↓
Build Matrix [Parallel] (3-5 min each)
    ├─ Windows
    │   ├─ Obfuscate (PyArmor)
    │   ├─ Package (PyApp)
    │   └─ Create .zip
    ├─ macOS
    │   ├─ Obfuscate (PyArmor)
    │   ├─ Package (PyApp)
    │   └─ Create .tar.gz
    └─ Linux
        ├─ Obfuscate (PyArmor)
        ├─ Package (PyApp)
        └─ Create .tar.gz
    ↓
Upload Artifacts
    ├─ windows-x64-package
    ├─ macos-universal-package
    └─ linux-x64-package
```

## 📦 Download Your Binaries

### From Actions Tab

1. Click **Actions** → Recent workflow run
2. Scroll to **Artifacts** section
3. Download platform packages
4. Each package contains:
   - Standalone binary
   - Documentation
   - Configuration template
   - SHA256 checksum

### From Releases (Tags Only)

```bash
# Create a release
git tag v1.1.0
git push origin v1.1.0

# Automatically creates GitHub Release with:
# ✓ All platform binaries
# ✓ Release notes
# ✓ Checksums
```

## 🔒 Security Features

| Feature | Status | Description |
|---------|--------|-------------|
| Vulnerability Scan | ✅ Auto | Checks all dependencies |
| Secret Detection | ✅ Auto | Scans for hardcoded keys |
| Code Obfuscation | ✅ Auto | PyArmor protection |
| Integrity Check | ✅ Auto | SHA256 checksums |

## 🛠️ Common Tasks

### Build Specific Version

```bash
git tag v1.2.0 -m "Release 1.2.0"
git push origin v1.2.0
```

### Manual Build Trigger

1. Go to **Actions** tab
2. Select **Build & Release** workflow
3. Click **Run workflow** → Select branch → **Run**

### Download Latest Build

```bash
# Using GitHub CLI
gh run download

# Or manually from Actions → Artifacts
```

### Test Before Release

```bash
# Build on feature branch
git checkout -b feature/new-feature
git push origin feature/new-feature

# Trigger manual build on that branch
# Actions → Run workflow → Select feature/new-feature
```

## 🚨 Troubleshooting

### Build Failed - Security Audit

**Issue**: Vulnerabilities detected

**Fix**:
```bash
pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip-audit --fix
```

### Build Failed - PyArmor

**Issue**: License not found

**Fix**: Add `PYARMOR_LICENSE` secret (see Setup Step 1)

### Build Failed - Packaging

**Issue**: Missing dependencies

**Fix**: Update `requirements.txt` with all dependencies

### Can't Find Artifacts

**Issue**: Build succeeded but no artifacts

**Fix**: Check the **Artifacts** section at bottom of workflow run page

## 📊 Verify Your Build

### 1. Check Workflow Status

```bash
# Using GitHub CLI
gh run list

# Or visit:
# https://github.com/USERNAME/REPO/actions
```

### 2. Verify Checksums

```bash
# Download package and checksum
# Then verify:
sha256sum -c windows-x64-package.zip.sha256

# macOS/Linux:
shasum -a 256 -c macos-universal-package.tar.gz.sha256
```

### 3. Test Binary

```bash
# Extract package
unzip windows-x64-package.zip
# or
tar -xzf macos-universal-package.tar.gz

# Run binary
./OA-OrientationAutomator
```

## 🎯 Next Steps

### For First Release

- [ ] Add `PYARMOR_LICENSE` secret
- [ ] Push to `main` branch
- [ ] Verify builds complete successfully
- [ ] Download and test all platform binaries
- [ ] Tag first release: `v1.1.0`

### For Production

- [ ] Add code signing certificates (Windows/macOS)
- [ ] Configure automatic deployment
- [ ] Set up release notifications
- [ ] Add build status badge to README

### For Team

- [ ] Share `README_GITHUB_CICD.md` with team
- [ ] Document release process
- [ ] Set up branch protection rules
- [ ] Configure required status checks

## 📖 Full Documentation

For detailed information, see:
- **README_GITHUB_CICD.md** - Complete setup guide
- **pyproject.toml** - Package configuration
- **.github/workflows/release.yml** - Workflow definition

## 🎉 You're Done!

Your automated build pipeline is now active. Every push to `main` will:
1. 🔍 Scan for security issues
2. 🔒 Obfuscate your code
3. 📦 Build platform binaries
4. 🚀 Upload for download

**Start by pushing to main and watch the magic happen!** ✨

---

**Questions?** Check the Actions tab for build logs.

