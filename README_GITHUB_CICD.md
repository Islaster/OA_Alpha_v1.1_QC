# GitHub CI/CD Setup Guide

## 🚀 Automated Build & Release Pipeline

This guide explains how to set up the GitHub Actions CI/CD pipeline for automated, secure, multi-platform distribution of OA - Orientation Automator.

## 📋 Overview

The CI/CD pipeline automatically:
1. ✅ **Security Audit** - Scans for vulnerabilities
2. 🔒 **Obfuscates Code** - Using PyArmor (commercial-grade protection)
3. 📦 **Creates Binaries** - Standalone executables for Windows, macOS, Linux
4. 🎯 **Distributes** - Uploads artifacts and creates GitHub releases

## 🔧 Setup Instructions

### Step 1: Add PyArmor License to GitHub Secrets

Your PyArmor license is required for commercial code obfuscation.

#### 1.1 Get Your PyArmor License

If you don't have a PyArmor license:
```bash
# Trial mode (free, limited)
# No license needed - pipeline will use trial mode

# Commercial license (recommended for production)
# Purchase from: https://pyarmor.dashingsoft.com/
```

#### 1.2 Add License to GitHub Secrets

1. **Go to your repository on GitHub**
   ```
   https://github.com/YOUR_USERNAME/YOUR_REPO
   ```

2. **Navigate to Settings → Secrets and variables → Actions**
   ```
   Repository → Settings (top menu)
   → Secrets and variables (left sidebar)
   → Actions
   ```

3. **Click "New repository secret"**

4. **Add the secret:**
   - **Name**: `PYARMOR_LICENSE`
   - **Value**: Your PyArmor license key (full text)
   
   Example format:
   ```
   # PyArmor License
   License-Type: <type>
   License-No: <number>
   License-To: <your-name>
   <rest of license content>
   ```

5. **Click "Add secret"**

### Step 2: Verify Workflow File

The workflow file should already be in place:
```
.github/workflows/release.yml
```

Check that it exists:
```bash
ls -la .github/workflows/release.yml
```

### Step 3: Configure PyProject.toml

The `pyproject.toml` file contains all packaging configuration. Verify it exists:
```bash
ls -la pyproject.toml
```

Update these fields with your information:
```toml
[project]
name = "oa-orientation-automator"
version = "1.1.0"
authors = [
    {name = "Your Name"}
]

[project.urls]
Homepage = "https://github.com/yourusername/yourrepo"
Repository = "https://github.com/yourusername/yourrepo"

[tool.pyapp.macos]
bundle-id = "com.yourcompany.orientationautomator"
```

### Step 4: Create .safety-policy.yml (Optional)

For dependency security scanning:
```bash
cat > .safety-policy.yml << 'EOF'
security:
  ignore-cvss-severity-below: 7
  ignore-cvss-unknown-severity: false
  continue-on-vulnerability-error: false

alert:
  - email: your-email@example.com
EOF
```

### Step 5: Push to GitHub

```bash
# Commit all files
git add .github/workflows/release.yml pyproject.toml
git commit -m "Add CI/CD pipeline for automated builds"

# Push to main branch (triggers build)
git push origin main
```

## 🎯 Triggering Builds

### Automatic Triggers

The pipeline runs automatically on:

1. **Push to main branch**
   ```bash
   git push origin main
   ```

2. **New version tag**
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

### Manual Trigger

You can also trigger builds manually:

1. Go to **Actions** tab on GitHub
2. Select **Build & Release** workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## 📦 Build Outputs

### Artifacts

After each successful build, you'll find artifacts for download:

- **windows-x64-package** - Windows executable + docs
- **macos-universal-package** - macOS binary + docs
- **linux-x64-package** - Linux binary + docs

**To download**:
1. Go to **Actions** tab
2. Click on the workflow run
3. Scroll to **Artifacts** section
4. Download the packages you need

### GitHub Releases

When you push a version tag (e.g., `v1.1.0`), the pipeline automatically:
1. Creates a GitHub Release
2. Uploads all platform binaries
3. Adds release notes
4. Includes SHA256 checksums

**To create a release**:
```bash
# Tag the release
git tag -a v1.1.0 -m "Release v1.1.0 - Security hardened edition"

# Push the tag
git push origin v1.1.0

# GitHub Actions will automatically create the release
```

## 🔒 Security Features

### Security Audit Phase

Before building, the pipeline:
- ✅ Runs `pip-audit` for 2025 vulnerability detection
- ✅ Runs `safety` for dependency security checks
- ✅ Scans for hardcoded secrets in source code
- ⚠️ Fails build if critical vulnerabilities found

### PyArmor Obfuscation

Code is obfuscated with:
- **BCC Mode** - Byte-code compilation
- **JIT Mode** - Just-in-time compilation
- **Private Mode** - Highest security level
- **Restrict Mode** - Prevents unauthorized use
- **Assert Checks** - Detects tampering

### PyApp Packaging

Binaries are:
- ✅ Standalone (no Python installation required)
- ✅ All dependencies bundled
- ✅ Platform-optimized
- ✅ Integrity-verified

## 🛠️ Customization

### Change Python Version

Edit `.github/workflows/release.yml`:
```yaml
env:
  PYTHON_VERSION: '3.12'  # Change to 3.10, 3.11, etc.
```

### Add/Remove Platforms

Edit the matrix in `.github/workflows/release.yml`:
```yaml
matrix:
  os: [windows-latest, macos-latest, ubuntu-latest]
  # Add: macos-13 for Intel Macs
  # Add: ubuntu-20.04 for older Linux
```

### Change Entry Point

For CLI instead of GUI, edit `pyproject.toml`:
```toml
[tool.pyapp]
entry-point = "main_processor:main"  # CLI
# entry-point = "gui_new:main"       # GUI
```

### Add Build Badge

Add to your README.md:
```markdown
![Build Status](https://github.com/USERNAME/REPO/workflows/Build%20&%20Release%20-%20Multi-Platform/badge.svg)
```

## 📊 Monitoring Builds

### View Build Logs

1. Go to **Actions** tab
2. Click on a workflow run
3. Click on a job (e.g., "Build windows-latest")
4. View detailed logs for each step

### Build Failure Troubleshooting

**Security Audit Failed**:
- Check pip-audit output for vulnerabilities
- Update dependencies: `pip install --upgrade -r requirements.txt`

**Obfuscation Failed**:
- Verify PYARMOR_LICENSE secret is set
- Check PyArmor is compatible with your code
- Review PyArmor logs in build output

**Packaging Failed**:
- Check that all dependencies are listed
- Verify entry point is correct
- Review PyApp/PyInstaller logs

## 🔐 Secret Management

### Required Secrets

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `PYARMOR_LICENSE` | PyArmor commercial license | Optional* |
| `GITHUB_TOKEN` | GitHub API token | Auto-provided |

*Trial mode works without license but has limitations

### Optional Secrets

| Secret Name | Description | When Needed |
|-------------|-------------|-------------|
| `APPLE_CERTIFICATE` | macOS code signing | macOS distribution |
| `APPLE_CERTIFICATE_PASSWORD` | Certificate password | macOS distribution |
| `WINDOWS_CERTIFICATE` | Windows code signing | Windows distribution |

### Adding Secrets

```bash
# Method 1: GitHub Web UI
# Settings → Secrets and variables → Actions → New repository secret

# Method 2: GitHub CLI
gh secret set PYARMOR_LICENSE < license.txt
```

## 📝 Build Configuration Files

### Key Files

```
.github/workflows/release.yml  - CI/CD pipeline definition
pyproject.toml                 - Package configuration
requirements.txt               - Python dependencies
requirements-security.txt      - Security dependencies
.safety-policy.yml            - Security policy (optional)
```

### Verification Checklist

- [ ] `PYARMOR_LICENSE` secret added to GitHub
- [ ] `pyproject.toml` configured with your details
- [ ] `release.yml` workflow file in place
- [ ] All requirements.txt files up to date
- [ ] No hardcoded secrets in source code
- [ ] `.env.example` included (not `.env`)

## 🚀 First Build

### Quick Start

```bash
# 1. Add your license to GitHub Secrets (see Step 1)

# 2. Commit and push
git add -A
git commit -m "Setup CI/CD pipeline"
git push origin main

# 3. Watch the build
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# 4. Download artifacts when complete
# Go to: Actions → Click workflow run → Artifacts section
```

### Create First Release

```bash
# Tag the release
git tag -a v1.1.0 -m "First automated release"
git push origin v1.1.0

# GitHub Actions will:
# ✓ Build for all platforms
# ✓ Obfuscate code
# ✓ Create binaries
# ✓ Create GitHub Release
# ✓ Upload all artifacts
```

## 📖 Additional Resources

### Documentation
- PyArmor: https://pyarmor.readthedocs.io/
- PyApp: https://ofek.dev/pyapp/
- GitHub Actions: https://docs.github.com/actions

### Support
- Check workflow logs for errors
- Review security audit output
- Verify all secrets are set correctly

## ⚠️ Important Notes

### Before First Build

1. ✅ **Add PYARMOR_LICENSE secret** (or accept trial limitations)
2. ✅ **Update pyproject.toml** with your information
3. ✅ **Test locally** before pushing to GitHub
4. ✅ **Verify no secrets** in source code

### Production Considerations

- 🔒 Use **PyArmor commercial license** for production
- 🔐 Add **code signing** for Windows/macOS distribution
- 📝 Update **version numbers** in pyproject.toml
- 🏷️ Create **release tags** for version tracking

### Security Best Practices

- ✅ Never commit `.env` file
- ✅ Use GitHub Secrets for all sensitive data
- ✅ Review security audit results before release
- ✅ Keep dependencies updated
- ✅ Test binaries on each platform

## 🎉 Success!

Once configured, every push to main automatically:
1. 🔍 Scans for vulnerabilities
2. 🔒 Obfuscates your code
3. 📦 Builds platform-specific binaries
4. 🚀 Creates downloadable artifacts

**Your secure, automated distribution pipeline is ready!** 🎯

---

**Questions?** Check the workflow logs in the Actions tab for detailed information.

**Issues?** Verify all secrets are set and configuration files are correct.

