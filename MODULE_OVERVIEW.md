# Module Overview - OA Orientation Automator

## Quick Reference Guide

### 🎯 Where to Find Things

| What You Need | Where to Look |
|---------------|---------------|
| Calculate bounding box | `src/core/bounding_box.py` |
| Load 3D file | `src/io/file_loader.py` |
| Export 3D file | `src/io/file_exporter.py` |
| Optimize rotation | `src/optimization/optimizer.py` |
| Generate rotation candidates | `src/optimization/rotation_generator.py` |
| PCA alignment | `src/optimization/pca_aligner.py` |
| Position at ground | `src/positioning/ground_positioner.py` |
| Learn from rotations | `src/learning/rotation_learner.py` |
| GUI main window | `src/gui/main_window.py` |
| GUI styling | `src/gui/theme.py` |
| Find Blender | `src/gui/blender_finder.py` |
| Background processing | `src/gui/workers.py` |
| Path utilities | `src/utils/paths.py` |
| Configuration | `src/utils/config_manager.py` |
| Debugging | `src/utils/debugger.py` |

## 📦 Module Details

### Core Modules (`src/core/`)

#### `bounding_box.py`
**Purpose**: Calculate axis-aligned bounding boxes (AABB)

**Key Functions**:
- `get_aabb_metrics(obj, sample_rate=1)` - Get complete AABB info
- `get_bounding_box_volume(obj)` - Get volume and dimensions
- `get_bounding_box_size(obj)` - Get just the volume
- `get_min_z(obj)` - Get minimum Z coordinate
- `get_center_xy(obj)` - Get XY center point

**Features**:
- Numpy acceleration when available
- Pure Python fallback
- Handles large meshes efficiently

**Example**:
```python
from src.core.bounding_box import get_aabb_metrics

metrics = get_aabb_metrics(obj)
print(f"Volume: {metrics['volume']}")
print(f"Dimensions: {metrics['dims']}")  # (width, depth, height)
print(f"Footprint: {metrics['footprint']}")  # XY area
```

---

#### `rotation.py`
**Purpose**: Rotation utilities and conversions

**Key Functions**:
- `degrees_to_radians(degrees)` - Convert degrees to radians tuple
- `radians_to_degrees(radians)` - Convert radians/Euler to degrees tuple
- `apply_rotation(obj, euler)` - Apply rotation to object
- `euler_to_matrix(euler)` - Convert Euler to 4x4 matrix
- `matrix_to_euler(matrix)` - Convert 4x4 matrix to Euler

**Example**:
```python
from src.core.rotation import degrees_to_radians, radians_to_degrees

rad = degrees_to_radians((90, 0, 45))  # (1.57, 0, 0.78)
deg = radians_to_degrees(obj.rotation_euler)  # (90.0, 0.0, 45.0)
```

---

#### `mesh_operations.py`
**Purpose**: Mesh queries and scene updates

**Key Functions**:
- `get_mesh_vertices(obj)` - Get all vertices in world space
- `get_face_areas(obj)` - Get face data (area, normal, center)
- `ensure_object_selected(obj)` - Select and activate object
- `force_scene_update()` - Force Blender scene update
- `force_object_update(obj)` - Force specific object update

**Example**:
```python
from src.core.mesh_operations import force_object_update, get_mesh_vertices

force_object_update(obj)  # Ensure transforms are current
vertices = get_mesh_vertices(obj)  # Get all vertex positions
```

---

### IO Modules (`src/io/`)

#### `file_loader.py`
**Purpose**: Load 3D files in various formats

**Key Functions**:
- `load_object(filepath)` - Load any supported 3D file

**Supported Formats**:
- `.obj` - Wavefront OBJ
- `.fbx` - Autodesk FBX
- `.ply` - Stanford PLY
- `.blend` - Blender files
- `.gltf` / `.glb` - glTF

**Features**:
- Automatic format detection
- Multiple Blender version compatibility
- Fallback methods for each format

**Example**:
```python
from src.io.file_loader import load_object

obj = load_object("model.obj")
if obj:
    print(f"Loaded: {obj.name}")
```

---

#### `file_exporter.py`
**Purpose**: Export 3D files in various formats

**Key Functions**:
- `export_object(obj, path, format=None, use_selection=True)` - Export object
- `export_collection_objects(collection_name, base_path, format)` - Export collection

**Supported Formats**: Same as loader

**Example**:
```python
from src.io.file_exporter import export_object

export_object(obj, "output.fbx")  # Auto-detect format
export_object(obj, "output.blend", format='blend')  # Explicit format
```

---

### Optimization Modules (`src/optimization/`)

#### `optimizer.py`
**Purpose**: Main rotation optimization algorithm

**Key Class**: `RotationOptimizer`

**Methods**:
- `__init__(obj, config, z_only=False)` - Initialize optimizer
- `optimize(learned_presets=None, max_time=600)` - Run optimization

**Strategy**:
1. Try learned presets (if provided)
2. Coarse grid search (45° steps)
3. Medium refinement (15° steps)
4. Fine refinement (5° steps)
5. PCA alignment (if enabled)
6. Fine-tuning (gradient descent)

**Example**:
```python
from src.optimization.optimizer import RotationOptimizer

optimizer = RotationOptimizer(obj, config)
best_rotation, reduction = optimizer.optimize()
print(f"Best: {best_rotation}, Reduction: {reduction:.1f}%")
```

---

#### `rotation_generator.py`
**Purpose**: Generate rotation candidates at various granularities

**Key Class**: `RotationGenerator`

**Methods**:
- `generate_coarse()` - 45° step rotations
- `generate_medium(center, radius=45, step=15)` - Medium search
- `generate_fine(center, radius=15, step=5)` - Fine search
- `generate_pca_variants(pca_euler)` - PCA + 90° variants

**Example**:
```python
from src.optimization.rotation_generator import RotationGenerator

gen = RotationGenerator(z_only=False, fast_mode=False)
coarse = gen.generate_coarse()  # List of (x,y,z) tuples in degrees
```

---

#### `pca_aligner.py`
**Purpose**: PCA-based rotation alignment

**Key Functions**:
- `calculate_pca_rotation(obj)` - Calculate PCA-based rotation with smart Z-flip

**Features**:
- Uses Principal Component Analysis
- Smart bottom footprint detection
- Pitch fine-tuning to minimize height

**Example**:
```python
from src.optimization.pca_aligner import calculate_pca_rotation

pca_euler = calculate_pca_rotation(obj)
if pca_euler:
    obj.rotation_euler = pca_euler
```

---

### Positioning Module (`src/positioning/`)

#### `ground_positioner.py`
**Purpose**: Position objects at ground zero

**Key Functions**:
- `position_at_ground_zero(obj)` - Position with bottom at Z=0, centered XY
- `move_to_origin_simple(obj)` - Simple positioning method

**Example**:
```python
from src.positioning.ground_positioner import position_at_ground_zero

position_at_ground_zero(obj)  # Bottom at Z=0, centered at X=0, Y=0
```

---

### Learning Module (`src/learning/`)

#### `rotation_learner.py`
**Purpose**: Learn from successful rotations

**Key Class**: `RotationLearner`

**Methods**:
- `save_rotation(name, type, rotation, reduction)` - Save successful rotation
- `get_presets_for_object(name, type)` - Get learned presets
- `get_common_presets(min_samples=3)` - Get commonly successful rotations
- `forget_object(name, type)` - Remove learned data

**Example**:
```python
from src.learning.rotation_learner import RotationLearner

learner = RotationLearner("rotation_presets.json")
learner.save_rotation("model.obj", "furniture", (90, 0, 45), 25.5)
presets = learner.get_presets_for_object("model.obj", "furniture")
```

---

### GUI Modules (`src/gui/`)

#### `main_window.py`
**Purpose**: Main GUI application window

**Key Class**: `MainWindow` (extends QMainWindow)

**Features**:
- Dark theme
- Blender path selection
- Input file selection
- Processing options
- Background processing with progress

---

#### `theme.py`
**Purpose**: Qt styling and theming

**Key Functions**:
- `get_dark_theme_stylesheet()` - Main dark theme
- `get_button_style_secondary()` - Secondary button style
- `get_button_style_primary()` - Primary button style

---

#### `blender_finder.py`
**Purpose**: Find and manage Blender installation

**Key Functions**:
- `find_blender()` - Auto-detect Blender installation
- `load_saved_blender_path()` - Load saved path
- `save_blender_path(path)` - Save path for future use

**Example**:
```python
from src.gui.blender_finder import find_blender

blender = find_blender()
if blender:
    print(f"Found Blender at: {blender}")
```

---

#### `workers.py`
**Purpose**: Background processing threads

**Key Classes**:
- `WorkerSignals` - Qt signals for thread communication
- `ProcessWorker` - Background worker for Blender processing

---

### Utility Modules (`src/utils/`)

#### `paths.py`
**Purpose**: Cross-platform path handling

**Key Functions**:
- `normalize_path(path_str)` - Normalize for cross-platform compatibility
- `get_app_dir()` - Get application directory
- `ensure_directory_exists(filepath)` - Create parent directories

**Example**:
```python
from src.utils.paths import normalize_path, get_app_dir

path = normalize_path("/path/to/file")  # Works on Windows, Mac, Linux
app_dir = get_app_dir()  # Works for script and frozen exe
```

---

#### `config_manager.py`
**Purpose**: Configuration and JSON file management

**Key Functions**:
- `load_json_file(filepath, default=None)` - Load JSON with fallback
- `save_json_file(filepath, data)` - Save JSON

**Key Class**: `ConfigManager`

**Example**:
```python
from src.utils.config_manager import ConfigManager

config = ConfigManager("config.json")
rotation_config = config.get("rotation", {})
config.set("debug.enabled", True)
config.save()
```

---

#### `debugger.py`
**Purpose**: Debugging and logging

**Key Class**: `Debugger`

**Key Functions**:
- `get_debugger(enabled=True, **kwargs)` - Get/create global debugger
- `reset_debugger()` - Reset global debugger

**Example**:
```python
from src.utils.debugger import get_debugger

debugger = get_debugger(enabled=True, log_file="debug.txt")
debugger.log("Processing started")
debugger.checkpoint("phase_1_complete")
```

---

## 🔌 Entry Points

### `gui_new.py`
Refactored GUI entry point
```bash
python gui_new.py
```

### `main_processor.py`
Refactored CLI entry point (simplified, focused)
```bash
blender --background --python main_processor.py -- input.obj
```

---

## 🧪 Testing Guide

Each module can be tested independently:

```python
# Test bounding box calculation
from src.core.bounding_box import get_aabb_metrics
metrics = get_aabb_metrics(test_obj)
assert metrics['volume'] > 0

# Test rotation conversion
from src.core.rotation import degrees_to_radians, radians_to_degrees
rad = degrees_to_radians((90, 0, 0))
deg = radians_to_degrees(rad)
assert deg == (90, 0, 0)

# Test file loading
from src.io.file_loader import load_object
obj = load_object("test.obj")
assert obj is not None

# Test configuration
from src.utils.config_manager import ConfigManager
config = ConfigManager("test_config.json")
assert config.get("rotation") is not None
```

---

## 📖 Import Cheat Sheet

```python
# Core
from src.core.bounding_box import get_aabb_metrics
from src.core.rotation import degrees_to_radians, radians_to_degrees
from src.core.mesh_operations import force_object_update

# IO
from src.io.file_loader import load_object
from src.io.file_exporter import export_object

# Optimization
from src.optimization.optimizer import RotationOptimizer
from src.optimization.rotation_generator import RotationGenerator
from src.optimization.pca_aligner import calculate_pca_rotation

# Positioning
from src.positioning.ground_positioner import position_at_ground_zero

# Learning
from src.learning.rotation_learner import RotationLearner

# Utils
from src.utils.paths import normalize_path, get_app_dir
from src.utils.config_manager import ConfigManager
from src.utils.debugger import get_debugger
```

---

## 🎯 Common Tasks

### Task: Optimize a 3D object

```python
from src.io.file_loader import load_object
from src.optimization.optimizer import RotationOptimizer
from src.positioning.ground_positioner import position_at_ground_zero

# Load
obj = load_object("model.obj")

# Optimize
optimizer = RotationOptimizer(obj, config={})
best_rotation, reduction = optimizer.optimize()

# Position
position_at_ground_zero(obj)

print(f"Optimized! Reduction: {reduction:.1f}%")
```

### Task: Learn from a successful rotation

```python
from src.learning.rotation_learner import RotationLearner

learner = RotationLearner()
learner.save_rotation(
    object_name="chair.obj",
    object_type="furniture",
    rotation_degrees=(90, 0, 45),
    bbox_reduction=28.5
)
```

### Task: Find Blender installation

```python
from src.gui.blender_finder import find_blender

blender = find_blender()
if blender:
    print(f"Blender found: {blender}")
else:
    print("Blender not found automatically")
```

---

**Total Modules**: 17  
**Total Lines of Code**: ~2,500 (well-organized!)  
**Average Module Size**: ~147 lines  
**Largest Module**: 300 lines (`optimizer.py`)  

**All modules are focused, testable, and maintainable!** ✨

