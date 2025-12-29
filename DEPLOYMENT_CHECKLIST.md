# 🚀 Deployment Checklist

## Pre-Deployment Verification

### ✅ 1. Run Verification Script

```bash
python3 verify_cicd_setup.py
```

**Expected Result**: All green checkmarks (✓)

**What it checks**:
- [ ] GitHub Actions workflow file exists
- [ ] pyproject.toml configured correctly
- [ ] Entry points (gui_new.py, main_processor.py) exist
- [ ] All requirements files present
- [ ] Security files (.env.example, .gitignore, etc.)
- [ ] Documentation complete
- [ ] Source structure intact

---

### ✅ 2. GitHub Repository Setup

- [ ] Repository created on GitHub (private or public)
- [ ] Code pushed to repository
- [ ] Actions enabled (Settings → Actions → Allow all actions)
- [ ] Branch protection rules configured (optional)

---

### ✅ 3. Add PyArmor License to GitHub Secrets

**Steps**:
1. Go to: `https://github.com/USERNAME/REPO/settings/secrets/actions`
2. Click "New repository secret"
3. **Name**: `PYARMOR_LICENSE`
4. **Value**: [Paste your PyArmor license content]
5. Click "Add secret"

**If you don't have a license**:
- [ ] Accept trial mode (automatic, but limited protection)
- [ ] Or purchase from: https://pyarmor.dashingsoft.com/

**Verification**:
- [ ] Secret appears in list (value hidden)
- [ ] Secret name is exactly `PYARMOR_LICENSE` (case-sensitive)

---

### ✅ 4. Security Audit

**Check for vulnerabilities**:
```bash
pip install pip-audit safety
pip-audit --desc
safety check
```

**Fix any issues**:
```bash
pip install --upgrade -r requirements.txt
pip-audit --fix
```

- [ ] No critical vulnerabilities (CVSS 7+)
- [ ] All dependencies up-to-date
- [ ] No hardcoded secrets in code

---

### ✅ 5. Configuration Files

**Verify these files exist and are correct**:

- [ ] `.github/workflows/release.yml` - CI/CD workflow
- [ ] `pyproject.toml` - Package configuration
- [ ] `requirements.txt` - Runtime dependencies
- [ ] `requirements-security.txt` - Security dependencies
- [ ] `requirements-build.txt` - Build tools
- [ ] `.safety-policy.yml` - Security policy
- [ ] `.gitignore` - Excludes .env, *.log, venv, __pycache__
- [ ] `env.example` - Environment template (NO REAL SECRETS)

**Verify entry points**:
- [ ] `gui_new.py` - GUI entry point exists
- [ ] `main_processor.py` - CLI entry point exists

---

## Deployment Steps

### 🚀 Option A: Deploy to Main Branch

**For continuous deployment of latest code**:

```bash
# 1. Commit all changes
git add .
git commit -m "Add CI/CD pipeline for automated builds"

# 2. Push to main
git push origin main

# 3. Monitor build
# Go to: https://github.com/USERNAME/REPO/actions
```

**Checklist**:
- [ ] Changes committed
- [ ] Pushed to main branch
- [ ] Workflow triggered automatically
- [ ] Build in progress (Actions tab shows running workflow)

---

### 🏷️ Option B: Create Release (Recommended)

**For versioned releases with GitHub Release page**:

```bash
# 1. Ensure code is committed and pushed
git add .
git commit -m "Release v1.1.0 - Production ready"
git push origin main

# 2. Create and push tag
git tag -a v1.1.0 -m "Release v1.1.0 - Production ready with CI/CD"
git push origin v1.1.0

# 3. GitHub Actions automatically:
# ✓ Builds all platforms
# ✓ Creates GitHub Release
# ✓ Uploads all artifacts
# ✓ Generates release notes
```

**Checklist**:
- [ ] Tag created with semantic versioning (vX.Y.Z)
- [ ] Tag pushed to GitHub
- [ ] Workflow triggered
- [ ] GitHub Release created automatically (check Releases tab)

---

## Build Monitoring

### ✅ Watch the Build

**Go to Actions tab**: `https://github.com/USERNAME/REPO/actions`

**What to watch for**:

1. **Security Audit Job** (~30 seconds)
   - [ ] pip-audit passes
   - [ ] safety check passes
   - [ ] Secret scanning passes

2. **Build Matrix Jobs** (~5 min each, parallel)
   - [ ] Windows build completes
   - [ ] macOS build completes
   - [ ] Linux build completes

3. **Artifact Upload** (~30 seconds)
   - [ ] windows-x64-package uploaded
   - [ ] macos-universal-package uploaded
   - [ ] linux-x64-package uploaded

4. **Release Creation** (if tag, ~10 seconds)
   - [ ] GitHub Release created
   - [ ] All artifacts attached

**Total time**: ~5-6 minutes

---

## Post-Build Verification

### ✅ 1. Download Artifacts

**From Actions** (every build):
1. Go to Actions tab
2. Click on workflow run (green checkmark)
3. Scroll to "Artifacts" section (bottom of page)
4. Download platform packages

**From Releases** (tagged builds only):
1. Go to Releases tab
2. Find your version (e.g., v1.1.0)
3. Download Assets

**Checklist**:
- [ ] Downloaded windows-x64-package.zip
- [ ] Downloaded macos-universal-package.tar.gz
- [ ] Downloaded linux-x64-package.tar.gz
- [ ] Downloaded .sha256 checksum files

---

### ✅ 2. Verify Checksums

**Windows**:
```powershell
certutil -hashfile windows-x64-package.zip SHA256
# Compare output with .sha256 file
```

**macOS/Linux**:
```bash
shasum -a 256 -c macos-universal-package.tar.gz.sha256
# Should show: OK
```

**Checklist**:
- [ ] Windows checksum verified
- [ ] macOS checksum verified
- [ ] Linux checksum verified

---

### ✅ 3. Test Binaries on Each Platform

**Windows**:
```bash
# Extract
unzip windows-x64-package.zip

# Run
cd windows-x64-package
OA-OrientationAutomator.exe
```

**macOS**:
```bash
# Extract
tar -xzf macos-universal-package.tar.gz

# Remove quarantine
cd macos-universal-package
xattr -cr OA-OrientationAutomator

# Run
./OA-OrientationAutomator
```

**Linux**:
```bash
# Extract
tar -xzf linux-x64-package.tar.gz

# Make executable
cd linux-x64-package
chmod +x OA-OrientationAutomator

# Run
./OA-OrientationAutomator
```

**Checklist**:
- [ ] Windows binary runs without errors
- [ ] macOS binary runs without errors
- [ ] Linux binary runs without errors
- [ ] No Python installation required
- [ ] GUI launches correctly
- [ ] Basic functionality works

---

### ✅ 4. Test Configuration

**Create .env file**:
```bash
cp env.example .env
# Edit .env with real values (if needed)
```

**Test that app loads configuration**:
- [ ] App reads .env file
- [ ] Settings applied correctly
- [ ] No hardcoded secrets in binary

---

## Troubleshooting

### ❌ Build Failed - Security Audit

**Error**: "Vulnerabilities detected"

**Fix**:
```bash
pip install --upgrade -r requirements.txt
pip-audit --fix
git commit -am "Update dependencies to fix vulnerabilities"
git push origin main
```

---

### ❌ Build Failed - PyArmor Error

**Error**: "License not found" or "License invalid"

**Fix Option 1** (Trial mode):
- Accept trial mode limitations
- Build will continue with basic obfuscation

**Fix Option 2** (Add license):
1. Verify secret name is exactly `PYARMOR_LICENSE`
2. Verify secret value is complete license text
3. Re-run workflow

---

### ❌ Build Succeeded but No Artifacts

**Issue**: Can't find artifacts after successful build

**Fix**:
1. Go to Actions tab
2. Click on the specific workflow run
3. Scroll to **bottom** of page
4. Look for **Artifacts** section (not in logs)
5. Click artifact name to download

---

### ❌ Binary Won't Run

**macOS**: "App is damaged and can't be opened"
```bash
xattr -cr OA-OrientationAutomator
```

**Linux**: "Permission denied"
```bash
chmod +x OA-OrientationAutomator
```

**Windows**: "Missing VCRUNTIME140.dll"
- Download and install: [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

---

## Success Criteria

### ✅ Deployment is successful when:

**Build Quality**:
- [ ] All security checks pass
- [ ] All three platforms build successfully
- [ ] No errors in build logs
- [ ] Build completes in under 10 minutes

**Artifacts**:
- [ ] All three platform packages available
- [ ] SHA256 checksums provided
- [ ] Documentation included in packages
- [ ] File sizes reasonable (30-50 MB compressed)

**Functionality**:
- [ ] Binaries run on all platforms
- [ ] No Python installation required
- [ ] GUI/CLI works correctly
- [ ] Configuration loads from .env

**Distribution**:
- [ ] Artifacts downloadable from Actions
- [ ] (If tagged) GitHub Release created
- [ ] Release notes generated
- [ ] Download links work

---

## Post-Deployment

### ✅ 1. Update Main README

Add build status badge:

```markdown
![Build Status](https://github.com/USERNAME/REPO/workflows/Build%20&%20Release%20-%20Multi-Platform/badge.svg)
```

Replace `USERNAME` and `REPO`.

**Checklist**:
- [ ] Badge added to README
- [ ] README updated with release info
- [ ] Links to documentation added

---

### ✅ 2. Announce Release

**Internal**:
- [ ] Share with team
- [ ] Update internal documentation
- [ ] Notify stakeholders

**External** (if public):
- [ ] Announcement post
- [ ] Update website
- [ ] Social media (if applicable)

---

### ✅ 3. Monitor & Iterate

**Set up monitoring**:
- [ ] GitHub Actions email notifications
- [ ] Slack/Discord webhooks (optional)
- [ ] Build status dashboard

**Plan next steps**:
- [ ] Collect user feedback
- [ ] Plan next release
- [ ] Add automated tests (if needed)
- [ ] Consider code signing (Windows/macOS)

---

## Quick Reference

### Key Commands

```bash
# Verify setup
python3 verify_cicd_setup.py

# Deploy to main
git push origin main

# Create release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# Test locally
./build_local.sh

# Security audit
pip-audit --desc
safety check

# Verify checksum
shasum -a 256 -c package.tar.gz.sha256
```

### Key URLs

```
Actions: https://github.com/USERNAME/REPO/actions
Releases: https://github.com/USERNAME/REPO/releases
Settings: https://github.com/USERNAME/REPO/settings
Secrets: https://github.com/USERNAME/REPO/settings/secrets/actions
```

### Key Files

```
.github/workflows/release.yml   - CI/CD workflow
pyproject.toml                  - Package config
requirements*.txt               - Dependencies
.gitignore                      - Excluded files
env.example                     - Config template
```

---

## Documentation

### Quick Guides
- **README_DEPLOYMENT.md** - 3-step deployment
- **CICD_QUICKSTART.md** - 5-minute setup
- **CICD_CHEATSHEET.md** - Command reference

### Comprehensive Guides
- **README_GITHUB_CICD.md** - Complete documentation
- **LOCAL_BUILD_GUIDE.md** - Local testing
- **GITHUB_ACTIONS_SUMMARY.md** - Implementation details

### This Checklist
- **DEPLOYMENT_CHECKLIST.md** - This file

---

## Final Checklist

Before considering deployment complete:

- [ ] ✅ Verification script passes
- [ ] ✅ PyArmor license in GitHub Secrets (or trial mode accepted)
- [ ] ✅ Security audit clean
- [ ] ✅ Code pushed to GitHub
- [ ] ✅ Workflow triggered
- [ ] ✅ All platforms built successfully
- [ ] ✅ Artifacts downloaded
- [ ] ✅ Checksums verified
- [ ] ✅ Binaries tested on all platforms
- [ ] ✅ Configuration tested
- [ ] ✅ Documentation updated
- [ ] ✅ Team notified

---

## 🎉 You're Done!

**Once all items are checked, your automated CI/CD pipeline is live and operational!**

**Every push to main will now automatically**:
1. 🔍 Scan for security vulnerabilities
2. 🔒 Obfuscate code with PyArmor
3. 📦 Build standalone binaries for Windows, macOS, Linux
4. ✅ Generate checksums
5. 🚀 Upload artifacts for download

**No manual intervention required!**

---

*Deployment Checklist v1.0*  
*Last updated: December 29, 2025*  
*CI/CD Pipeline Version: 1.0*

