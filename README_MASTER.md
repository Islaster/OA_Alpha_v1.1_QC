# OA - Orientation Automator v1.1 🎯

## Secure, Automated, Cross-Platform 3D Model Optimization

[![Build Status](https://img.shields.io/badge/build-automated-brightgreen)](https://github.com)
[![Security](https://img.shields.io/badge/security-2025%20hardened-blue)](SECURITY.md)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-orange)](README_DEPLOYMENT.md)

**OA - Orientation Automator** is a production-ready application that automatically optimizes 3D model orientations to minimize bounding box volume. Built with enterprise-grade security, automated CI/CD, and cross-platform distribution.

---

## ✨ Features

### Core Functionality
- 🎯 **Automatic Rotation Optimization** - Minimize bounding box through intelligent rotation algorithms
- 🧠 **Machine Learning** - Learns from successful optimizations for faster future processing
- 📐 **PCA Alignment** - Principal Component Analysis for initial orientation detection
- 🎨 **Modern GUI** - PySide6-based interface with dark theme
- 💻 **CLI Support** - Command-line interface for automation and scripting
- 🔄 **Multi-Format Support** - OBJ, FBX, BLEND, PLY, GLTF, GLB

### Security (2025 Standards)
- 🔒 **Code Obfuscation** - PyArmor commercial-grade protection
- 🔐 **Secrets Management** - python-dotenv with .env configuration
- ✅ **Input Validation** - Strict allowlist-based sanitization
- 🛡️ **Secure Subprocess** - No shell injection vulnerabilities
- 🔑 **AES-256 Encryption** - For local data at rest
- 📝 **Hardened Error Handling** - No information leakage

### DevOps & Distribution
- 🚀 **Automated CI/CD** - GitHub Actions multi-platform builds
- 📦 **Standalone Binaries** - No Python installation required
- 🌍 **Cross-Platform** - Windows, macOS, Linux
- 🔍 **Security Scanning** - Automated vulnerability detection
- ✔️ **Integrity Verification** - SHA256 checksums
- 📊 **Build Artifacts** - Downloadable packages for each platform

---

## 🚀 Quick Start

### For End Users (Pre-built Binaries)

1. **Download** the package for your platform from [Releases](../../releases)
2. **Extract** the archive
3. **Run** the application:
   ```bash
   # Windows
   OA-OrientationAutomator.exe
   
   # macOS/Linux
   ./OA-OrientationAutomator
   ```

No Python or dependencies required!

### For Developers (From Source)

```bash
# Clone repository
git clone https://github.com/yourusername/oa-orientation-automator.git
cd oa-orientation-automator

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-security.txt

# Run GUI
python gui_new.py

# Or run CLI with Blender
blender --background --python main_processor.py -- input.obj
```

### For CI/CD Deployment

See [**README_DEPLOYMENT.md**](README_DEPLOYMENT.md) for complete deployment guide.

```bash
# Quick deploy:
# 1. Add PYARMOR_LICENSE to GitHub Secrets
# 2. Push to main
git push origin main
# 3. Download artifacts from Actions tab
```

---

## 📚 Documentation Index

### 🎯 Getting Started
- **[README_DEPLOYMENT.md](README_DEPLOYMENT.md)** - 3-step deployment guide
- **[CICD_QUICKSTART.md](CICD_QUICKSTART.md)** - 5-minute CI/CD setup
- **[README_REFACTORED.md](README_REFACTORED.md)** - Original project documentation

### 🔧 Development
- **[LOCAL_BUILD_GUIDE.md](LOCAL_BUILD_GUIDE.md)** - Build locally before CI/CD
- **[MODULE_OVERVIEW.md](MODULE_OVERVIEW.md)** - Code structure and modules
- **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Refactoring methodology
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Refactoring results

### 🔐 Security
- **[SECURITY.md](SECURITY.md)** - Security posture and practices
- **[SECURITY_IMPLEMENTATION_SUMMARY.md](SECURITY_IMPLEMENTATION_SUMMARY.md)** - Security changes
- **[SECURITY_QUICK_REFERENCE.md](SECURITY_QUICK_REFERENCE.md)** - Best practices
- **[README_SECURITY_HARDENED.md](README_SECURITY_HARDENED.md)** - Security guide

### 🚀 CI/CD & Deployment
- **[README_GITHUB_CICD.md](README_GITHUB_CICD.md)** - Complete CI/CD documentation
- **[CICD_CHEATSHEET.md](CICD_CHEATSHEET.md)** - Command reference
- **[CICD_IMPLEMENTATION_COMPLETE.md](CICD_IMPLEMENTATION_COMPLETE.md)** - Technical details

### 📊 Analysis
- **[BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md)** - Refactoring metrics

---

## 🏗️ Architecture

### Project Structure

```
OA_Alpha_v1.1_QC/
├── src/                           # Modular source code
│   ├── core/                      # Core algorithms
│   │   ├── bounding_box.py        # AABB calculations
│   │   ├── rotation.py            # Rotation utilities
│   │   └── mesh_operations.py     # Mesh processing
│   ├── optimization/              # Optimization algorithms
│   │   ├── optimizer.py           # Main optimization logic
│   │   ├── rotation_generator.py  # Rotation sampling
│   │   └── pca_aligner.py         # PCA alignment
│   ├── io/                        # File I/O
│   │   ├── file_loader.py         # Import 3D files
│   │   └── file_exporter.py       # Export 3D files
│   ├── gui/                       # GUI components
│   │   ├── main_window.py         # Main application window
│   │   ├── workers.py             # Background processing
│   │   ├── theme.py               # Visual styling
│   │   └── blender_finder.py      # Blender detection
│   ├── security/                  # Security features
│   │   ├── validators.py          # Input validation
│   │   ├── encryption.py          # Data encryption
│   │   ├── secure_config.py       # Config management
│   │   └── error_handler.py       # Error handling
│   ├── learning/                  # Machine learning
│   │   └── rotation_learner.py    # Preset learning
│   ├── positioning/               # Object positioning
│   │   └── ground_positioner.py   # Ground alignment
│   └── utils/                     # Utilities
│       ├── config_manager.py      # JSON config
│       ├── debugger.py            # Debug logging
│       └── paths.py               # Path normalization
├── .github/workflows/             # CI/CD automation
│   └── release.yml                # Multi-platform builds
├── gui_new.py                     # GUI entry point
├── main_processor.py              # CLI entry point
├── pyproject.toml                 # Package configuration
├── requirements*.txt              # Dependencies
└── [Documentation files]          # This README and guides
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **GUI** | PySide6 | Modern Qt-based interface |
| **3D Engine** | Blender (bpy) | 3D model processing |
| **Optimization** | Custom algorithms + NumPy | Rotation optimization |
| **Security** | cryptography, python-dotenv | Secure-by-default standards |
| **Obfuscation** | PyArmor | Code protection |
| **Packaging** | PyApp, PyInstaller | Standalone binaries |
| **CI/CD** | GitHub Actions | Automated builds |

---

## 🔐 Security

### Protection Layers

```
┌─────────────────────────────────────┐
│  User Input                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Input Validation (Allowlist)       │
│  ✓ File path sanitization           │
│  ✓ Type/length/format checking      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Secure Processing                  │
│  ✓ No shell injection               │
│  ✓ No eval/exec                     │
│  ✓ Encrypted local data             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Code Obfuscation (PyArmor)         │
│  ✓ BCC + JIT compilation            │
│  ✓ Private mode                     │
│  ✓ Tampering detection              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Hardened Error Handling            │
│  ✓ Generic user messages            │
│  ✓ Detailed internal logs           │
│  ✓ No information leakage           │
└─────────────────────────────────────┘
```

### Security Compliance

✅ **2025 Secure-by-Default Standards**  
✅ **OWASP Top 10 Mitigations**  
✅ **Automated Vulnerability Scanning**  
✅ **No Hardcoded Secrets**  
✅ **AES-256 Encryption at Rest**  
✅ **Secure Random Number Generation**  

See [**SECURITY.md**](SECURITY.md) for complete security documentation.

---

## 🚀 CI/CD Pipeline

### Automated Build Process

```
Push to main/tag
    ↓
Security Audit (30s)
    ├─ pip-audit (vulnerabilities)
    ├─ safety check (dependencies)
    └─ secret scanning
    ↓
Parallel Builds (~5 min each)
    ├─ Windows → .exe
    ├─ macOS → Universal binary
    └─ Linux → Binary
    ↓
Artifact Upload
    ├─ Platform packages (.zip/.tar.gz)
    └─ SHA256 checksums
    ↓
GitHub Release (on tags)
    ├─ Release notes
    └─ All artifacts attached
```

### Build Triggers

| Action | Result |
|--------|--------|
| Push to `main` | Build artifacts |
| Push tag `v1.x.x` | Build + GitHub Release |
| Manual trigger | On-demand build |

**Setup Time**: 3 minutes  
**Build Time**: 5-6 minutes  
**Platforms**: 3 (Windows, macOS, Linux)  

See [**README_DEPLOYMENT.md**](README_DEPLOYMENT.md) for deployment guide.

---

## 📊 Performance

### Optimization Results

| Metric | Value |
|--------|-------|
| Average bounding box reduction | 20-40% |
| Processing time (typical) | 10-60 seconds |
| Learning system improvement | 50% faster on known objects |
| Multi-phase optimization | Coarse → Medium → Fine → Gradient descent |

### Build Performance

| Phase | Duration |
|-------|----------|
| Security audit | 30s |
| Code obfuscation | 60s |
| Binary packaging | 120s |
| **Total build time** | **~5 min** |

---

## 🧪 Testing

### Verification Tools

```bash
# Verify CI/CD setup
python3 verify_cicd_setup.py

# Build locally
./build_local.sh

# Security audit
pip-audit --desc
safety check

# Verify package integrity
shasum -a 256 -c package.tar.gz.sha256
```

### Test Coverage

- ✅ Input validation tests
- ✅ Security scanning (automated in CI)
- ✅ Multi-platform build verification
- ✅ Integrity verification (checksums)
- ✅ End-to-end GUI/CLI testing

---

## 🤝 Contributing

### Development Workflow

1. **Clone** the repository
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** following security guidelines
4. **Test locally**: `./build_local.sh`
5. **Push**: `git push origin feature/new-feature`
6. **Trigger manual build** from Actions tab to test
7. **Create pull request**

### Coding Standards

- ✅ Follow PEP 8 style guide
- ✅ Use type hints where applicable
- ✅ Document all public functions
- ✅ Use security best practices (see `SECURITY.md`)
- ✅ Test locally before pushing
- ✅ Run `verify_cicd_setup.py` before committing

---

## 📋 Requirements

### Runtime (End Users)

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Disk Space**: 500 MB for application + space for 3D models

**Note**: Pre-built binaries include all dependencies. No Python required!

### Development (Developers)

- **Python**: 3.10 or higher
- **Blender**: 3.0+ (for bpy module)
- **Dependencies**: See `requirements.txt`
- **Build Tools**: See `requirements-build.txt`

### CI/CD (Automation)

- **GitHub Account**: With Actions enabled
- **PyArmor License**: Optional (trial mode works)
- **Secrets**: `PYARMOR_LICENSE` in GitHub Secrets

---

## 🔧 Configuration

### Environment Variables

Create `.env` from `env.example`:

```bash
cp env.example .env
```

Configure as needed:

```env
# API Keys (if using AI features)
OA_AI_API_KEY=your-api-key-here

# Application Settings
OA_DEBUG=false
OA_LOG_LEVEL=INFO

# Blender Path (optional, auto-detected)
BLENDER_PATH=/path/to/blender
```

### Configuration File

`config.json`:
```json
{
  "rotation": {
    "coarse_step": 45,
    "medium_step": 15,
    "fine_step": 5,
    "gradient_step": 2
  },
  "learning": {
    "enable_learning": true,
    "min_confidence": 0.7
  },
  "logging": {
    "log_level": "INFO",
    "log_file": "processing_log.txt"
  }
}
```

---

## 📝 Usage Examples

### GUI Usage

1. Launch application
2. Click "Browse" to select 3D model
3. (Optional) Adjust settings
4. Click "Process"
5. Wait for optimization
6. Output saved automatically

### CLI Usage

```bash
# Basic usage
blender --background --python main_processor.py -- input.obj

# With options
blender --background --python main_processor.py -- \
    input.obj \
    --type furniture \
    --report output_report.json \
    --debug

# Skip learning
blender --background --python main_processor.py -- \
    input.obj \
    --no-learning
```

### Programmatic Usage

```python
from src.main_processor import BoundingBoxProcessor

# Initialize
processor = BoundingBoxProcessor("config.json")

# Process file
result = processor.process_file(
    "input.obj",
    object_name="my_model",
    object_type="furniture",
    use_learning=True,
    save_rotation=True
)

# Access results
print(f"Reduction: {result['bbox_reduction_percent']:.2f}%")
print(f"Time: {result['processing_time']:.2f}s")
```

---

## 🐛 Troubleshooting

### Common Issues

**"Blender not found"**
- Install Blender 3.0+ from blender.org
- Or set `BLENDER_PATH` in `.env`

**"PyArmor license error" (CI/CD)**
- Add license to GitHub Secrets
- Or accept trial mode limitations

**"Binary won't run"**
- macOS: `xattr -cr OA-OrientationAutomator`
- Linux: `chmod +x OA-OrientationAutomator`
- Windows: Install VC++ Redistributable

**"Build failed - vulnerabilities"**
```bash
pip install --upgrade -r requirements.txt
pip-audit --fix
```

See [**CICD_CHEATSHEET.md**](CICD_CHEATSHEET.md) for more troubleshooting.

---

## 🎯 Roadmap

### Version 1.1 (Current)
- ✅ Modular refactoring
- ✅ Security hardening (2025 standards)
- ✅ Automated CI/CD
- ✅ Cross-platform binaries

### Version 1.2 (Planned)
- [ ] GPU acceleration
- [ ] Batch processing
- [ ] Cloud integration
- [ ] Advanced ML models

### Version 2.0 (Future)
- [ ] Web interface
- [ ] Plugin system
- [ ] Real-time preview
- [ ] Multi-object optimization

---

## 📄 License

**Proprietary** - All rights reserved.

This software is obfuscated and distributed as standalone binaries. Source code access is restricted to authorized developers.

For licensing inquiries, contact: [your-email@example.com]

---

## 🙏 Acknowledgments

- **Blender Foundation** - For the amazing Blender and bpy API
- **Qt/PySide6** - For the modern GUI framework
- **PyArmor** - For code protection
- **GitHub** - For Actions and hosting
- **Python Community** - For excellent libraries

---

## 📞 Support

### Documentation
- 📖 **[Complete Documentation Index](#-documentation-index)** above
- 🚀 **[Deployment Guide](README_DEPLOYMENT.md)** for setup
- 🔐 **[Security Guide](SECURITY.md)** for security info

### Getting Help
- 📧 **Email**: support@yourcompany.com
- 🐛 **Issues**: [GitHub Issues](../../issues)
- 💬 **Discussions**: [GitHub Discussions](../../discussions)

### Quick Links
- 🌟 **[Releases](../../releases)** - Download binaries
- 📊 **[Actions](../../actions)** - Build status
- 🔒 **[Security Policy](SECURITY.md)** - Security practices

---

## 🎉 Status

**Version**: 1.1.0  
**Status**: ✅ Production Ready  
**Build**: Automated  
**Security**: 2025 Hardened  
**Platforms**: Windows, macOS, Linux  

---

<div align="center">

**OA - Orientation Automator**

Secure • Automated • Cross-Platform

[Get Started](README_DEPLOYMENT.md) • [Documentation](#-documentation-index) • [Releases](../../releases)

---

*Built with ❤️ using Python, Blender, and modern DevOps practices*

</div>

