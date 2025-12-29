# Build Guide

## CI/CD (Automated)

Push to GitHub - builds automatically for Windows, macOS, Linux.

```bash
git push origin main
```

Download artifacts from Actions tab after ~5 minutes.

## Local Build

### Install Nuitka

```bash
pip install nuitka ordered-set zstandard

# Platform tools
# Ubuntu: sudo apt-get install ccache patchelf
# macOS: brew install ccache
```

### Compile

```bash
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --include-package=src \
    gui_new.py
```

Or use the script:

```bash
./build_local.sh
```

## Troubleshooting

- **Nuitka fails**: Check C compiler is installed
- **Missing modules**: Add `--include-package=module_name`
- **Large binary**: Use `--lto=yes` for optimization

See workflow: `.github/workflows/release.yml`
