# 🚀 Deployment Guide - OA Orientation Automator

## Quick Start (3 Steps)

### 1️⃣ Add PyArmor License to GitHub

```
Your Repository on GitHub
→ Settings (top tab)
→ Secrets and variables (left sidebar)
→ Actions
→ New repository secret
   Name: PYARMOR_LICENSE
   Value: [paste your PyArmor license]
→ Add secret
```

**Don't have a license?** The pipeline will use trial mode automatically. Get a commercial license at: https://pyarmor.dashingsoft.com/

### 2️⃣ Push to GitHub

```bash
git add .
git commit -m "Add CI/CD pipeline for automated builds"
git push origin main
```

### 3️⃣ Watch the Build

```
GitHub → Actions tab → Build & Release workflow
Wait ~5-6 minutes
→ Download artifacts from the Artifacts section
```

**That's it!** You now have obfuscated binaries for Windows, macOS, and Linux.

---

## 📦 What You Get

### Every Build Produces:

```
windows-x64-package.zip         (~35 MB)
├── OA-OrientationAutomator.exe
├── README.txt
├── env.example
└── docs/

macos-universal-package.tar.gz  (~40 MB)
├── OA-OrientationAutomator
├── README.txt
├── env.example
└── docs/

linux-x64-package.tar.gz        (~35 MB)
├── OA-OrientationAutomator
├── README.txt
├── env.example
└── docs/

+ SHA256 checksums for each package
```

---

## 🏷️ Creating Releases

### Automatic Release (Recommended)

```bash
# Tag your code
git tag -a v1.1.0 -m "Release v1.1.0 - Production ready"
git push origin v1.1.0

# GitHub Actions automatically:
# ✓ Builds all platforms
# ✓ Creates GitHub Release
# ✓ Uploads all artifacts
# ✓ Generates release notes
```

### Manual Release

1. Go to Actions tab
2. Click "Build & Release"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow" button

---

## 🔐 Security Features

Your binaries are protected with:

✅ **PyArmor Obfuscation**
- Byte-code compilation (BCC)
- JIT compilation
- Private mode (highest security)
- Restrict mode (prevent unauthorized use)
- Tampering detection

✅ **Security Scanning**
- pip-audit (2025 vulnerabilities)
- safety check (dependency security)
- Hardcoded secret detection

✅ **Secrets Management**
- No hardcoded credentials
- `.env` file for configuration
- GitHub Secrets for CI/CD

✅ **Secure Subprocess**
- No shell injection vulnerabilities
- Array-based command execution

✅ **Error Handling**
- Generic messages to users
- Detailed logs internally
- No information leakage

---

## 📥 Downloading Builds

### From Actions (Every Build)

1. **Go to Actions tab** on GitHub
2. **Click on a workflow run** (green checkmark)
3. **Scroll to Artifacts** section (bottom of page)
4. **Download** platform packages

### From Releases (Tagged Builds Only)

1. **Go to Releases tab** on GitHub
2. **Find your version** (e.g., v1.1.0)
3. **Download Assets** (all platforms available)

---

## ✅ Verification

### Before Deploying

Run the verification script:

```bash
python3 verify_cicd_setup.py
```

Should show all green checkmarks (✓).

### After Downloading

Verify package integrity:

```bash
# Windows
certutil -hashfile windows-x64-package.zip SHA256
# Compare with .sha256 file

# macOS/Linux
shasum -a 256 -c macos-universal-package.tar.gz.sha256
```

---

## 📊 Build Status

Add this badge to your README:

```markdown
![Build Status](https://github.com/USERNAME/REPO/workflows/Build%20&%20Release%20-%20Multi-Platform/badge.svg)
```

Replace `USERNAME` and `REPO` with your GitHub username and repository name.

---

## 🛠️ Configuration

### Customize Build Platforms

Edit `.github/workflows/release.yml`:

```yaml
matrix:
  os: [windows-latest, macos-latest, ubuntu-latest]
  # Add more: macos-13, ubuntu-20.04, etc.
```

### Change Python Version

Edit `.github/workflows/release.yml`:

```yaml
env:
  PYTHON_VERSION: '3.12'  # Change to 3.10, 3.11, etc.
```

### Switch Entry Point (GUI vs CLI)

Edit `pyproject.toml`:

```toml
[tool.pyapp]
# For GUI (default):
entry-point = "gui_new:main"

# For CLI:
entry-point = "main_processor:main"
```

---

## 🧪 Local Testing

Before pushing to GitHub, test locally:

```bash
# Run verification
python3 verify_cicd_setup.py

# Build locally
./build_local.sh

# Test the binary
./dist/obfuscated/dist/OA-OrientationAutomator
```

See `LOCAL_BUILD_GUIDE.md` for detailed instructions.

---

## 🚨 Troubleshooting

### Build Fails - Security Audit

**Error**: Vulnerabilities detected

**Fix**:
```bash
pip install --upgrade -r requirements.txt
pip-audit --fix
git commit -am "Update dependencies"
git push
```

### Build Fails - PyArmor

**Error**: License not found

**Fix**: Add `PYARMOR_LICENSE` to GitHub Secrets (or accept trial mode)

### Artifacts Not Showing

**Issue**: Build succeeded but no artifacts

**Fix**: Check **Artifacts** section at bottom of workflow run page (not in logs)

### Binary Won't Run

**macOS**: "App is damaged"
```bash
xattr -cr OA-OrientationAutomator
```

**Linux**: "Permission denied"
```bash
chmod +x OA-OrientationAutomator
```

**Windows**: "Missing DLL"
- Install Visual C++ Redistributable

---

## 📚 Documentation

| Document | Use Case |
|----------|----------|
| `CICD_QUICKSTART.md` | 5-minute setup guide |
| `README_GITHUB_CICD.md` | Complete documentation |
| `CICD_CHEATSHEET.md` | Command reference |
| `LOCAL_BUILD_GUIDE.md` | Test builds locally |
| `CICD_IMPLEMENTATION_COMPLETE.md` | Technical details |

---

## 🎯 Deployment Checklist

### Pre-Deployment

- [ ] `PYARMOR_LICENSE` added to GitHub Secrets (optional)
- [ ] `verify_cicd_setup.py` passes
- [ ] `.env.example` has no real secrets
- [ ] `.gitignore` excludes `.env`
- [ ] Documentation reviewed

### Testing

- [ ] Push to `main` triggers build
- [ ] All platforms build successfully
- [ ] Artifacts downloadable
- [ ] Checksums verified
- [ ] Binaries run on each platform

### Go Live

- [ ] Tag release (e.g., `v1.1.0`)
- [ ] GitHub Release created automatically
- [ ] All artifacts attached
- [ ] Release notes accurate
- [ ] Download links work

---

## 🎉 You're Ready!

Your automated, secure, cross-platform deployment pipeline is configured and ready to use.

**Next Step**: Push to GitHub and let CI/CD do the work!

```bash
git push origin main
```

Then watch the Actions tab as your code is:
1. 🔍 Security scanned
2. 🔒 Obfuscated with PyArmor
3. 📦 Packaged for Windows, macOS, Linux
4. 🚀 Uploaded and ready for distribution

**Questions?** See the full documentation in `README_GITHUB_CICD.md`

---

*Automated CI/CD Pipeline v1.0*  
*Security Standard: 2025 Secure-by-Default*  
*Build Time: ~5-6 minutes*  
*Platforms: Windows, macOS, Linux*

