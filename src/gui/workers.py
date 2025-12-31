"""
Background worker threads for GUI.
"""
import os
import subprocess
import threading
import logging
import platform
from pathlib import Path
from PySide6.QtCore import Signal, QObject

from src.security.validators import validate_command_args, ValidationError
from src.utils.paths import get_app_dir


logger = logging.getLogger(__name__)


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
        from src.security.validators import validate_file_path
        from src.utils.paths import find_data_file
        
        try:
            
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
                # Log the full error details
                import logging
                import platform
                from src.utils.paths import get_app_dir
                
                logger = logging.getLogger(__name__)
                
                # Get error output from Blender
                error_output = result.stderr or result.stdout or "Unknown error"
                
                # Log full error details
                logger.error(f"Blender processing failed with return code {result.returncode}")
                logger.error(f"Blender command: {' '.join(cmd)}")
                logger.error(f"Blender stderr: {result.stderr[:1000] if result.stderr else '(empty)'}")
                logger.error(f"Blender stdout: {result.stdout[:1000] if result.stdout else '(empty)'}")
                
                # Ensure log is flushed
                for handler in logger.handlers:
                    handler.flush()
                
                # Truncate error message for display
                sanitized_error = error_output[:500].replace('\n', ' ').replace('\r', ' ')
                
                # Get log file location for user message
                if platform.system() == 'Darwin':
                    home_dir = os.path.expanduser("~")
                    log_file = os.path.join(home_dir, "Library", "Logs", "OA-OrientationAutomator", "processing_log.txt")
                else:
                    log_file = os.path.join(get_app_dir(), "processing_log.txt")
                
                self.signals.finished.emit(False, 
                    f"Processing failed.\n\n"
                    f"Log file: {log_file}\n\n"
                    f"Please check the log file for details.")
                
        except subprocess.TimeoutExpired:
            self.signals.finished.emit(False, 
                "Processing timed out. The file may be too large or complex.")
        except ValidationError as ve:
            self.signals.finished.emit(False, f"Validation error: {ve}")
        except Exception as e:
            # Log full error details with traceback
            # Get the actual log file location (same as setup_logging uses)
            if platform.system() == 'Darwin':
                home_dir = os.path.expanduser("~")
                log_file = os.path.join(home_dir, "Library", "Logs", "OA-OrientationAutomator", "processing_log.txt")
            else:
                log_file = os.path.join(get_app_dir(), "processing_log.txt")
            
            # Log full error with traceback
            logger.error("Worker error occurred:", exc_info=True)
            
            # Ensure log is flushed
            for handler in logger.handlers:
                handler.flush()
            
            error_msg = (
                f"An unexpected error occurred.\n\n"
                f"Log file location:\n{log_file}\n\n"
                f"Please check the log file for details."
            )
            self.signals.finished.emit(False, error_msg)

