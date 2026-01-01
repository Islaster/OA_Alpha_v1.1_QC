"""
src/io/file_exporter.py

Blender export utilities with backwards-compatible public API.

✅ Key behavior this file enforces (to match your working legacy behavior):
- If you export a .blend, it will ALSO attempt to export baked collections
  (Optimized_Baked / Auto_Ground_Baked / Manual_Ground_Baked) as a mesh file,
  just like the old bounding_box_minimizer.py did.

This is specifically to prevent the “only .blend exports” regression when the
caller only does: export_object(obj, "/path/out.blend")

Public API (safe for main_processor imports):
- export_object(...)              # required by main_processor
- export_collection_objects(...)
- export_baked_collections(...)
- sanity_check_baked_written(...)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Iterable, Optional, Sequence

import bpy

from src.security.validators import validate_file_path, ALLOWED_3D_FORMATS, ValidationError

logger = logging.getLogger(__name__)

# Substrings used by the legacy script when naming baked collections
BAKED_PATTERNS = ("Optimized_Baked", "Auto_Ground_Baked", "Manual_Ground_Baked")

# Suffixes used by the legacy script when exporting baked files
BAKED_SUFFIX_BY_PATTERN = {
    "Optimized_Baked": "_optimized_baked",
    "Auto_Ground_Baked": "_auto_ground_baked",
    "Manual_Ground_Baked": "_manual_ground_baked",
}


# -----------------------------------------------------------------------------
# Small utilities
# -----------------------------------------------------------------------------
def _normalize_ext(fmt_or_ext: Optional[str]) -> Optional[str]:
    """Accept 'obj' or '.obj' and return '.obj' lowercase."""
    if not fmt_or_ext:
        return None
    s = str(fmt_or_ext).strip().lower()
    if not s:
        return None
    return s if s.startswith(".") else f".{s}"


def _ensure_parent_dir(filepath: str | Path) -> None:
    Path(filepath).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _validate_export_path(output_path: str | Path, *, allowed_exts: set[str], purpose: str) -> str:
    try:
        validated = validate_file_path(
            output_path,
            purpose=purpose,
            must_exist=False,
            allowed_extensions=allowed_exts,
        )
        return str(validated)
    except ValidationError as e:
        logger.error(f"Invalid output path: {e}")
        raise


def _ensure_object_mode() -> None:
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        # Headless mode can be finicky; continue best-effort
        pass


def _force_update() -> None:
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
    except Exception:
        pass


def _select_objects(objs: Iterable[bpy.types.Object]) -> list[bpy.types.Object]:
    selected = [o for o in objs if o is not None]
    if not selected:
        return []

    _ensure_object_mode()

    try:
        bpy.ops.object.select_all(action="DESELECT")
    except Exception:
        pass

    for o in selected:
        try:
            o.hide_set(False)
        except Exception:
            pass
        try:
            o.select_set(True)
        except Exception:
            pass

    try:
        bpy.context.view_layer.objects.active = selected[-1]
    except Exception:
        pass

    _force_update()
    return selected


def _verify_written(filepath: str | Path, *, min_bytes: int = 16) -> None:
    p = Path(filepath)
    if not p.exists():
        raise RuntimeError(f"Export completed but file was not created: {p}")
    try:
        size = p.stat().st_size
        if size < min_bytes:
            raise RuntimeError(f"Export created an unexpectedly small file ({size} bytes): {p}")
    except OSError:
        # Existence is still a strong enough signal
        pass


def _ensure_addon_enabled(module_name: str) -> None:
    try:
        import addon_utils
        addon_utils.enable(module_name, default_set=True, persistent=True)
    except Exception as e:
        logger.debug(f"Could not enable addon {module_name}: {e}")


def _find_collection_by_pattern(pattern: str) -> Optional[bpy.types.Collection]:
    for col in bpy.data.collections:
        if pattern in col.name:
            return col
    return None


def _infer_baked_export_format(default: str = ".obj") -> str:
    """
    Determine which mesh format to use for baked exports.

    Priority:
    1) OA_BAKED_FORMAT env var ('.obj', 'fbx', etc)
    2) OA_EXPORT_FORMAT env var
    3) default ('.obj')
    """
    env = os.environ.get("OA_BAKED_FORMAT") or os.environ.get("OA_EXPORT_FORMAT")
    ext = _normalize_ext(env) if env else None
    if ext in (".obj", ".fbx", ".ply", ".gltf", ".glb"):
        return ext
    return _normalize_ext(default) or ".obj"


# -----------------------------------------------------------------------------
# Low-level exporters
# -----------------------------------------------------------------------------
def _export_blend(filepath: str) -> None:
    bpy.ops.wm.save_as_mainfile(filepath=filepath)


def _export_obj(filepath: str, use_selection: bool) -> None:
    # Blender 4/5 style
    try:
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            global_scale=1.0,
            apply_modifiers=True,
            export_triangulated_mesh=False,
        )
        return
    except (AttributeError, RuntimeError, TypeError) as e:
        logger.debug(f"OBJ 4/5 export failed ({e}); trying Blender 3.x export_scene.obj")

    # Blender 3.x style
    try:
        bpy.ops.export_scene.obj(
            filepath=filepath,
            use_selection=use_selection,
            use_materials=True,
            global_scale=1.0,
        )
        return
    except Exception as e2:
        logger.debug(f"OBJ 3.x export failed ({e2}); enabling io_scene_obj and retrying")

    _ensure_addon_enabled("io_scene_obj")
    bpy.ops.export_scene.obj(
        filepath=filepath,
        use_selection=use_selection,
        use_materials=True,
        global_scale=1.0,
    )


def _export_fbx(filepath: str, use_selection: bool) -> None:
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=use_selection,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
    )


def _export_ply(filepath: str, use_selection: bool) -> None:
    try:
        bpy.ops.wm.ply_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            global_scale=1.0,
        )
        return
    except (AttributeError, RuntimeError, TypeError) as e:
        logger.debug(f"PLY 4/5 export failed ({e}); trying Blender 3.x export_mesh.ply")

    try:
        bpy.ops.export_mesh.ply(filepath=filepath)
        return
    except Exception as e2:
        logger.debug(f"PLY 3.x export failed ({e2}); enabling io_mesh_ply and retrying")

    _ensure_addon_enabled("io_mesh_ply")
    bpy.ops.export_mesh.ply(filepath=filepath)


def _export_gltf(filepath: str, use_selection: bool) -> None:
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=use_selection,
        export_apply_modifiers=True,
    )


# -----------------------------------------------------------------------------
# Sanity check
# -----------------------------------------------------------------------------
def sanity_check_baked_written(
    expected_paths: Iterable[str | Path],
    *,
    wait_seconds: float = 0.25,
    min_bytes: int = 16,
) -> dict:
    """
    Post-export sanity check:
    - Confirms exported baked files exist and aren't tiny.
    - Raises RuntimeError if any are missing/too small.
    """
    paths = [Path(p) for p in expected_paths]
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    report = {"ok": [], "missing": [], "too_small": []}

    for p in paths:
        if not p.exists():
            report["missing"].append(str(p))
            continue
        try:
            size = p.stat().st_size
        except OSError:
            size = -1

        if 0 <= size < min_bytes:
            report["too_small"].append({"path": str(p), "size": size})
        else:
            report["ok"].append({"path": str(p), "size": size})

    if report["missing"] or report["too_small"]:
        raise RuntimeError(f"Baked export sanity check failed: {report}")

    return report


# -----------------------------------------------------------------------------
# Core baked export logic (matches legacy behavior)
# -----------------------------------------------------------------------------
def export_baked_collections(
    blend_path: str | Path,
    export_format: Optional[str] = None,
    *,
    validate: bool = True,
    require_at_least_one: Optional[bool] = None,
) -> dict:
    """
    Export baked collections in the specified format.

    Debug + safety:
      - Prints baked collections seen at export time.
      - If OA_REQUIRE_BAKED=1, will raise if none are exported.
      - If expected baked patterns aren't found, falls back to exporting ANY collection
        containing 'Baked' in its name (prevents naming-regression failures).

    Returns:
      {
        "export_format": ".obj",
        "searched_patterns": [...],
        "found_baked_collections": [...],
        "exported_paths": [...],
      }
    """
    base_path = str(Path(blend_path).with_suffix(""))
    ext = _normalize_ext(export_format) if export_format else _infer_baked_export_format()

    if ext not in (".obj", ".fbx", ".ply", ".gltf", ".glb"):
        raise ValueError(f"Unsupported baked export format: {ext}")

    # Strictness: env wins unless explicitly provided
    if require_at_least_one is None:
        require_at_least_one = os.environ.get("OA_REQUIRE_BAKED") in ("1", "true", "TRUE", "yes", "YES")

    # Snapshot: what baked collections exist RIGHT NOW?
    baked_like = []
    for c in bpy.data.collections:
        if "baked" in c.name.lower():
            try:
                baked_like.append((c.name, len(c.objects)))
            except Exception:
                baked_like.append((c.name, -1))

    # Always print this (goes to Blender stderr/stdout capture and is gold for debugging)
    print(f"BAKED DEBUG: collections containing 'Baked': {baked_like}", flush=True)

    searched_patterns = list(BAKED_PATTERNS)
    exported: list[str] = []
    found_names: list[str] = []

    # 1) Try the legacy patterns first
    pattern_hits: list[tuple[str, bpy.types.Collection]] = []
    for pattern in BAKED_PATTERNS:
        col = _find_collection_by_pattern(pattern)
        if col and len(col.objects) > 0:
            pattern_hits.append((pattern, col))

    # 2) Fallback: if no hits, export ANY baked-like collection names
    fallback_hits: list[bpy.types.Collection] = []
    if not pattern_hits:
        for c in bpy.data.collections:
            if "baked" in c.name.lower() and len(c.objects) > 0:
                fallback_hits.append(c)

    # Helper to export a selected collection to a path
    def _export_selected_collection(col: bpy.types.Collection, export_path: str) -> None:
        _select_objects(col.objects)
        if ext == ".obj":
            _export_obj(export_path, use_selection=True)
        elif ext == ".fbx":
            _export_fbx(export_path, use_selection=True)
        elif ext == ".ply":
            _export_ply(export_path, use_selection=True)
        elif ext in (".gltf", ".glb"):
            _export_gltf(export_path, use_selection=True)
        _force_update()
        _verify_written(export_path)

    # Export pattern hits
    for pattern, col in pattern_hits:
        found_names.append(col.name)

        suffix = BAKED_SUFFIX_BY_PATTERN.get(pattern, f"_{pattern.lower()}")
        export_path = f"{base_path}{suffix}{ext}"

        if validate:
            export_path = _validate_export_path(export_path, allowed_exts=ALLOWED_3D_FORMATS, purpose="export")
        _ensure_parent_dir(export_path)

        _export_selected_collection(col, export_path)
        exported.append(export_path)
        print(f"✓ Exported baked (pattern={pattern}): {Path(export_path).name}", flush=True)

    # Export fallback hits (only if patterns were missing)
    if not pattern_hits and fallback_hits:
        for col in fallback_hits:
            found_names.append(col.name)

            # slugify-ish suffix from collection name
            safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in col.name).strip("_")
            export_path = f"{base_path}_baked_{safe}{ext}"

            if validate:
                export_path = _validate_export_path(export_path, allowed_exts=ALLOWED_3D_FORMATS, purpose="export")
            _ensure_parent_dir(export_path)

            _export_selected_collection(col, export_path)
            exported.append(export_path)
            print(f"✓ Exported baked (fallback): {Path(export_path).name}", flush=True)

    # Final sanity check
    if require_at_least_one and not exported:
        raise RuntimeError(
            "No baked exports were produced.\n"
            f"searched_patterns={searched_patterns}\n"
            f"baked_collections_seen={baked_like}\n"
            "This usually means baked collections were never created OR were deleted/restored before export."
        )

    if exported:
        sanity_check_baked_written(exported)

    return {
        "export_format": ext,
        "searched_patterns": searched_patterns,
        "found_baked_collections": found_names,
        "exported_paths": exported,
    }


def export_collection_objects(
    collection_name: str,
    base_path: str | Path,
    export_format: str,
    *,
    validate: bool = True,
) -> Optional[str]:
    """
    Export all objects in a collection (first match contains collection_name).
    """
    ext = _normalize_ext(export_format)
    if not ext:
        raise ValueError("export_format is required (e.g. '.obj' or 'obj').")

    collection = None
    for col in bpy.data.collections:
        if collection_name in col.name:
            collection = col
            break

    if not collection or len(collection.objects) == 0:
        return None

    export_path = f"{str(Path(base_path))}{ext}"

    if validate:
        export_path = _validate_export_path(
            export_path,
            allowed_exts=ALLOWED_3D_FORMATS | {".blend"},
            purpose="export",
        )
    _ensure_parent_dir(export_path)

    _select_objects(collection.objects)

    try:
        if ext == ".blend":
            _export_blend(export_path)
        elif ext == ".obj":
            _export_obj(export_path, use_selection=True)
        elif ext == ".fbx":
            _export_fbx(export_path, use_selection=True)
        elif ext == ".ply":
            _export_ply(export_path, use_selection=True)
        elif ext in (".gltf", ".glb"):
            _export_gltf(export_path, use_selection=True)
        else:
            raise ValueError(f"Unsupported export format: {ext}")

        _force_update()
        _verify_written(export_path)
        return export_path
    except Exception as e:
        logger.warning(f"Failed to export collection {collection_name}: {e}", exc_info=True)
        return None


# -----------------------------------------------------------------------------
# REQUIRED public API: export_object
# -----------------------------------------------------------------------------
def export_object(
    obj: bpy.types.Object,
    output_path: str | Path,
    format: Optional[str] = None,
    use_selection: bool = True,
) -> str:
    """
    Export object to file.

    IMPORTANT:
    - This is the public API expected by main_processor.py.
    - If exporting a .blend, this will ALSO attempt baked mesh exports if baked
      collections exist (prevents "blend-only" regressions).

    Baked export format selection:
    - If `format` is a mesh format (.obj/.fbx/.ply/.gltf/.glb), use that
    - Otherwise fall back to env OA_BAKED_FORMAT / OA_EXPORT_FORMAT / default
    """
    out_path = str(output_path)

    # Validate output path for primary export
    out_path = _validate_export_path(
        out_path,
        allowed_exts=ALLOWED_3D_FORMATS | {".blend"},
        purpose="export",
    )
    _ensure_parent_dir(out_path)

    # Primary format (what we're writing to out_path)
    primary_ext = Path(out_path).suffix.lower()
    if format is not None:
        fmt_ext = _normalize_ext(format)
        if fmt_ext:
            primary_ext = fmt_ext

    # Setup selection/context
    if use_selection:
        _select_objects([obj])
    else:
        _ensure_object_mode()
        _force_update()

    # ---- Primary export ----
    if primary_ext == ".blend":
        _export_blend(out_path)
        _force_update()
        _verify_written(out_path, min_bytes=64)
        logger.info(f"Exported .blend -> {out_path}")

        # ---- Baked export (only after .blend) ----
        baked_ext = _normalize_ext(format)
        if baked_ext not in (".obj", ".fbx", ".ply", ".gltf", ".glb"):
            baked_ext = None  # allow exporter to infer from env/default

        # Snapshot baked collections at export time
        baked_snapshot = [(c.name, len(c.objects)) for c in bpy.data.collections if "baked" in c.name.lower()]
        print(f"BAKED DEBUG (at export time): {baked_snapshot}", flush=True)

        baked_result = export_baked_collections(
            blend_path=out_path,
            export_format=baked_ext,
            validate=True,
            require_at_least_one=None,
        )

        # Robustly read results (older/newer keys)
        found = baked_result.get("found_baked_collections") or baked_result.get("found_collections") or []
        exported = baked_result.get("exported_paths") or baked_result.get("exported") or []

        # Fail loudly only if baked collections exist but nothing was exported
        if found and not exported:
            raise RuntimeError(
                "Baked collections were found but no baked files were exported. "
                f"found={found} baked_result={baked_result}"
            )

    elif primary_ext == ".obj":
        _export_obj(out_path, use_selection=use_selection)
        _force_update()
        _verify_written(out_path)
        logger.info(f"Exported .obj -> {out_path}")

    elif primary_ext == ".fbx":
        _export_fbx(out_path, use_selection=use_selection)
        _force_update()
        _verify_written(out_path)
        logger.info(f"Exported .fbx -> {out_path}")

    elif primary_ext == ".ply":
        _export_ply(out_path, use_selection=use_selection)
        _force_update()
        _verify_written(out_path)
        logger.info(f"Exported .ply -> {out_path}")

    elif primary_ext in (".gltf", ".glb"):
        _export_gltf(out_path, use_selection=use_selection)
        _force_update()
        _verify_written(out_path)
        logger.info(f"Exported {primary_ext} -> {out_path}")

    else:
        raise ValueError(f"Unsupported format: {primary_ext}")

    return out_path
