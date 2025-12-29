# Blender Bounding Box Minimizer - Cross-Platform Version

A tool that optimizes 3D object orientation to minimize bounding box volume, running inside Blender.

## What This Tool Does

When you scan or create a 3D object, it often has an arbitrary orientation. The **axis-aligned bounding box** (the smallest rectangular box that can contain the object when aligned to X/Y/Z axes) can be much larger than necessary.

This tool finds the **optimal rotation** that minimizes this bounding box, which is useful for:
- **Shipping/packaging optimization** - smaller boxes = lower costs
- **Storage efficiency** - better stacking and organization
- **3D printing** - optimal bed placement
- **Game engines** - faster collision detection with tighter bounds

## Requirements

- **Blender 3.0+** (tested on 3.6, 4.0, 4.1, 4.2)
- **Python packages** (installed automatically by setup script):
  - `numpy` (for faster processing)
  - `scipy` (for advanced optimization)

## Quick Start

### Step 1: Install Blender

**Mac:**
```bash
brew install --cask blender
# Or download from https://www.blender.org/download/
```

**Windows:**
Download from https://www.blender.org/download/ and install.

**Linux:**
```bash
sudo snap install blender --classic
# Or: sudo apt install blender
```

### Step 2: Choose Your Interface

#### Option A: GUI (Recommended) 🖥️

**Mac/Linux:**
```bash
chmod +x setup_gui.sh run_gui.sh
./setup_gui.sh    # One-time setup (creates venv, installs PySide6)
./run_gui.sh      # Launch the GUI
```

**Windows:**
```cmd
setup_gui.bat     # One-time setup
run_gui.bat       # Launch the GUI
```

#### Option B: Command Line 💻

**Mac/Linux:**
```bash
chmod +x setup.sh run_optimizer.sh
./setup.sh        # One-time setup (installs into Blender's Python)
./run_optimizer.sh model.obj
```

**Windows:**
```cmd
setup.bat         # One-time setup
run_optimizer.bat model.obj
```

## Usage

### Basic Usage

Run from terminal using the provided scripts:

**Mac/Linux:**
```bash
./run_optimizer.sh input_file.obj
./run_optimizer.sh input_file.obj -o output_file.obj
```

**Windows:**
```cmd
run_optimizer.bat input_file.obj
run_optimizer.bat input_file.obj -o output_file.obj
```

**Direct Blender command (if needed):**
```bash
# Mac
/Applications/Blender.app/Contents/MacOS/Blender --background --python bounding_box_minimizer.py -- input_file.obj

# Windows
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python bounding_box_minimizer.py -- input_file.obj
```

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `input` | Input file path (obj, fbx, blend, ply, gltf) |
| `-o, --output` | Output file path |
| `-c, --config` | Configuration file (default: config.json) |
| `--no-ground` | Skip ground detection |
| `--no-learning` | Disable learning system |
| `--type` | Object type/category for learning |
| `--report` | Save processing report to JSON |
| `--debug` | Enable debug mode |

### Examples

**Mac/Linux:**
```bash
# Basic optimization
./run_optimizer.sh model.obj

# With custom output
./run_optimizer.sh model.obj -o model_optimized.obj

# Skip ground detection, just minimize bbox
./run_optimizer.sh model.obj --no-ground

# Save a detailed report
./run_optimizer.sh model.obj --report results.json

# Process multiple files
for f in *.obj; do ./run_optimizer.sh "$f"; done
```

**Windows:**
```cmd
REM Basic optimization
run_optimizer.bat model.obj

REM With custom output
run_optimizer.bat model.obj -o model_optimized.obj

REM Skip ground detection
run_optimizer.bat model.obj --no-ground

REM Process multiple files
for %f in (*.obj) do run_optimizer.bat %f
```

## Output

The tool creates a `.blend` file with multiple collections:

1. **1_Original** - Object as imported
2. **2_Optimized** - After rotation optimization
3. **3_Optimized_Baked** - With transforms applied to mesh (ready for export)
4. **4_Auto_Ground** - With ground detection (if enabled)
5. **5_Auto_Ground_Baked** - Ground version ready for export

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "rotation": {
    "common_presets": [-90, -45, 0, 45, 90, 180],
    "adaptive_steps": [15, 5, 1, 0.5, 0.1],
    "use_pca_initial_guess": true
  },
  "ground_detection": {
    "use_learned": true,
    "use_physics": true
  },
  "learning": {
    "enable_learning": true
  }
}
```

## Optimization Strategies

The tool uses multiple strategies in sequence:

1. **Learned Presets** - Uses successful rotations from previous runs
2. **Common Presets** - Tests standard angles (0°, 45°, 90°, etc.)
3. **PCA Alignment** - Uses Principal Component Analysis
4. **Scipy Optimization** - L-BFGS-B algorithm for fine-tuning
5. **Adaptive Grid Search** - Fine-tunes with decreasing step sizes

## Files Included

### GUI Files
| File | Description |
|------|-------------|
| `gui.py` | PySide6 GUI application |
| `setup_gui.sh` | Mac/Linux: Setup venv + install PySide6 |
| `setup_gui.bat` | Windows: Setup venv + install PySide6 |
| `run_gui.sh` | Mac/Linux: Launch GUI |
| `run_gui.bat` | Windows: Launch GUI |
| `requirements.txt` | Python dependencies |

### Command Line Files
| File | Description |
|------|-------------|
| `setup.sh` | Mac/Linux: Install deps into Blender's Python |
| `setup.bat` | Windows: Install deps into Blender's Python |
| `run_optimizer.sh` | Mac/Linux: Run optimizer CLI |
| `run_optimizer.bat` | Windows: Run optimizer CLI |

### Core Files
| File | Description |
|------|-------------|
| `bounding_box_minimizer.py` | Main optimization script (runs in Blender) |
| `rotation_optimizer.py` | Rotation optimization engine |
| `utils.py` | Utility functions |
| `debugger.py` | Debug logging |
| `config.json` | Configuration settings |

## Troubleshooting

### "bpy not available"
Make sure you're running the script through Blender, not directly with Python.

### Path issues
The Mac version uses `pathlib.Path` for cross-platform compatibility. All paths should work with forward slashes (`/`).

### Performance
For very large meshes (>1M vertices), ensure numpy is available for faster processing.

## Cross-Platform Notes

This version includes:
- Cross-platform path handling using `pathlib.Path`
- UTF-8 encoding for all file operations
- Auto-detection of Blender installation
- Setup scripts for both Windows and Mac/Linux
- Batch files and shell scripts for easy execution

## Environment Variables

You can set these environment variables to customize behavior:

| Variable | Description |
|----------|-------------|
| `BLENDER` | Path to Blender executable (overrides auto-detection) |

Example:
```bash
# Mac/Linux
export BLENDER=/custom/path/to/blender
./run_optimizer.sh model.obj

# Windows
set BLENDER=C:\Custom\Path\blender.exe
run_optimizer.bat model.obj
```

## License

Same as the original project.

