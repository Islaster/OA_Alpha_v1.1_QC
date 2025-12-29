# OA - Orientation Automator

Automated 3D model bounding box optimization with Nuitka compilation.

## Features

- 🎯 Automatic rotation optimization to minimize bounding box
- 🧠 Machine learning from successful optimizations
- 🎨 Modern GUI (PySide6)
- 💻 CLI support for automation
- 🔒 Security-hardened (2025 standards)
- 🚀 Compiled with Nuitka (native performance)

## Quick Start

### Download Pre-built Binaries

Go to [Releases](../../releases) and download for your platform.

### Run from Source

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-security.txt

# Run GUI
python gui_new.py

# Or CLI with Blender
blender --background --python main_processor.py -- input.obj
```

## Configuration

```bash
cp env.example .env
# Edit .env with your settings
```

## Building

See [BUILD.md](BUILD.md) for compilation instructions.

## Security

- Compiled to native machine code (Nuitka)
- No hardcoded secrets (use `.env`)
- Input validation and sanitization
- AES-256 encryption for local data

## License

Proprietary - All rights reserved.
