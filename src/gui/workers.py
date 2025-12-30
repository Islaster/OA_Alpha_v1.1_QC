"""
Background worker threads for GUI.
"""
import os
import subprocess
import threading
from pathlib import Path
from PySide6.QtCore import Signal, QObject


class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    finished = Signal(bool, str)
    progress = Signal(str)


class ProcessWorker(threading.Thread):
    """Background worker for running Blender processing."""
    
    def __init__(self, blender_path, input_file, script_dir, skip_learning=False):
        """
        Initialize worker.
        
        Args:
            blender_path: Path to Blender executable
            input_file: Input 3D file path
            script_dir: Directory containing scripts
            skip_learning: Skip using learned rotations
        """
        super().__init__()
        self.blender_path = blender_path
        self.input_file = input_file
        self.script_dir = script_dir
        self.skip_learning = skip_learning
        self.signals = WorkerSignals()
        self.daemon = True
    
    def run(self):
        """Run the processing task (SECURE VERSION)."""
        from src.security.validators import validate_file_path, validate_command_args, ValidationError
        from src.security.error_handler import sanitize_log_message
        
        try:
            # Find the script file (handles Nuitka data file placement)
            from src.utils.paths import find_data_file
            
            script_path = find_data_file("bounding_box_minimizer.py")
            
            # Fallback to script_dir if not found via find_data_file
            if not script_path or not os.path.exists(script_path):
                fallback_path = os.path.join(self.script_dir, "bounding_box_minimizer.py")
                if os.path.exists(fallback_path):
                    script_path = fallback_path
                else:
                    # Last resort: check current working directory
                    cwd_path = os.path.join(os.getcwd(), "bounding_box_minimizer.py")
                    if os.path.exists(cwd_path):
                        script_path = cwd_path
            
            # If still not found, provide helpful error
            if not script_path or not os.path.exists(script_path):
                error_msg = (
                    f"Could not find bounding_box_minimizer.py. "
                    f"Searched in: {self.script_dir}, {os.getcwd()}, and executable directory. "
                    f"Please ensure the file is included in the build."
                )
                self.signals.finished.emit(False, error_msg)
                return
            
            # Validate script path
            script_path = validate_file_path(
                script_path,
                purpose="script",
                must_exist=True
            )
            
            # Validate input file
            input_file_path = validate_file_path(
                self.input_file,
                purpose="input",
                must_exist=True
            )
            
            # Build command with validated paths
            # SECURITY: Using array-based subprocess (NOT shell=True)
            cmd = [
                str(self.blender_path),  # Converted to string for subprocess
                "--background",
                "--python", str(script_path),
                "--",
                str(input_file_path)
            ]
            
            # Always skip ground detection
            cmd.append("--no-ground")
            
            if self.skip_learning:
                cmd.append("--no-learning")
            
            # Validate command arguments (prevents injection)
            try:
                cmd = validate_command_args(cmd, purpose="Blender execution")
            except ValidationError as ve:
                self.signals.finished.emit(False, f"Security validation failed: {ve}")
                return
            
            self.signals.progress.emit("Running Blender...")
            
            # SECURITY: subprocess without shell=True (prevents command injection)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(self.script_dir),
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                input_dir = Path(self.input_file).parent
                self.signals.finished.emit(True,
                    f"Processing complete!\n\nOutput saved to:\n{input_dir}")
            else:
                # Sanitize error message before showing to user
                error = result.stderr or result.stdout or "Unknown error"
                sanitized_error = sanitize_log_message(error[:500])
                self.signals.finished.emit(False, 
                    f"Processing failed. Please check the log file for details.")
                
        except subprocess.TimeoutExpired:
            self.signals.finished.emit(False, 
                "Processing timed out. The file may be too large or complex.")
        except ValidationError as ve:
            self.signals.finished.emit(False, f"Validation error: {ve}")
        except Exception as e:
            # Generic error message (no internal details leaked)
            sanitized = sanitize_log_message(str(e))
            import logging
            logging.error(f"Worker error: {sanitized}")
            self.signals.finished.emit(False, 
                "An unexpected error occurred. Please check the log file.")

