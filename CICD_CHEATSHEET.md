# CI/CD Cheat Sheet

## 🚀 Quick Commands

### Initial Setup
```bash
# 1. Add secret to GitHub
# Repository → Settings → Secrets → Actions → New secret
# Name: PYARMOR_LICENSE

# 2. Push to trigger build
git push origin main
```

### Create Release
```bash
git tag v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0
```

### Manual Build
```bash
# Go to: Actions → Build & Release → Run workflow
```

### Download Artifacts
```bash
# Using GitHub CLI
gh run download

# Or: Actions → Click run → Artifacts section
```

## 📋 Build Triggers

| Action | Trigger | Output |
|--------|---------|--------|
| `git push origin main` | Auto | Artifacts only |
| `git push origin v1.x.x` | Auto | Release + Artifacts |
| Manual (Actions tab) | Manual | Artifacts only |

## 🔒 Security Checks

| Check | What It Does | Fail Behavior |
|-------|--------------|---------------|
| `pip-audit` | 2025 vulnerability scan | ❌ Fails build |
| `safety` | Dependency security | ⚠️ Warning only |
| Secret scan | Finds hardcoded keys | ❌ Fails build |

## 📦 Output Files

### Artifacts (Every Build)
```
windows-x64-package.zip
├── OA-OrientationAutomator.exe
├── README.txt
├── env.example
└── BUILD_INFO.txt

macos-universal-package.tar.gz
├── OA-OrientationAutomator
├── README.txt
├── env.example
└── BUILD_INFO.txt

linux-x64-package.tar.gz
├── OA-OrientationAutomator
├── README.txt
├── env.example
└── BUILD_INFO.txt
```

### Checksums
```
windows-x64-package.zip.sha256
macos-universal-package.tar.gz.sha256
linux-x64-package.tar.gz.sha256
```

## 🛠️ Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/release.yml` | Pipeline definition |
| `pyproject.toml` | Package config |
| `.safety-policy.yml` | Security rules |
| `requirements.txt` | Python deps |

## 🔧 Customization

### Change Python Version
```yaml
# In .github/workflows/release.yml
env:
  PYTHON_VERSION: '3.12'  # Change here
```

### Change Platforms
```yaml
# In .github/workflows/release.yml
matrix:
  os: [windows-latest, macos-latest, ubuntu-latest]
  # Add: macos-13, ubuntu-20.04, etc.
```

### GUI vs CLI
```toml
# In pyproject.toml
[tool.pyapp]
entry-point = "gui_new:main"       # GUI (default)
# entry-point = "main_processor:main"  # CLI
```

## 🚨 Troubleshooting

### Build Failed
```bash
# Check logs
# Actions → Click run → Click job → View logs

# Common fixes:
pip install --upgrade -r requirements.txt
pip-audit --fix
```

### No Artifacts
```bash
# Build must complete successfully
# Check: Actions → Run → Artifacts (bottom of page)
```

### License Error
```bash
# Add PYARMOR_LICENSE secret
# Or: Pipeline uses trial mode automatically
```

## 📊 Build Time

| Phase | Duration |
|-------|----------|
| Security Audit | ~30s |
| Windows Build | ~5 min |
| macOS Build | ~5 min |
| Linux Build | ~5 min |
| **Total** | **~5-6 min** |

*Builds run in parallel*

## 🎯 Status Badge

Add to README.md:
```markdown
![Build](https://github.com/USER/REPO/workflows/Build%20&%20Release/badge.svg)
```

## 📖 Full Docs

- **CICD_QUICKSTART.md** - 5-minute setup
- **README_GITHUB_CICD.md** - Complete guide
- **pyproject.toml** - All config options

## ⚡ Pro Tips

1. **Fast Iteration**: Push to feature branch, trigger manual build
2. **Test Locally**: `pyarmor gen src/` before committing
3. **Version Tags**: Always use semantic versioning (v1.2.3)
4. **Checksums**: Always verify downloads with .sha256 files
5. **Keep Updated**: Run `pip install --upgrade` regularly

---

**Ready?** → `git push origin main` 🚀

