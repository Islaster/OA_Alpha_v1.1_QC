"""
OA - Orientation Automator (Alpha) - PySide6 GUI
Cross-platform GUI using Qt for professional look and feel.
"""
import sys
import os
import subprocess
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QProgressBar, QCheckBox, QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject, Slot
from PySide6.QtGui import QFont


def get_app_dir():
    """Get the application directory - works for both script and frozen EXE."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def load_saved_blender_path():
    """Load Blender path from saved file if it exists."""
    app_dir = get_app_dir()
    path_file = os.path.join(app_dir, "blender_path.txt")
    if os.path.exists(path_file):
        try:
            with open(path_file, 'r') as f:
                saved_path = f.read().strip()
                if os.path.exists(saved_path):
                    return saved_path
        except:
            pass
    return None


def save_blender_path(blender_path):
    """Save Blender path for future use."""
    app_dir = get_app_dir()
    path_file = os.path.join(app_dir, "blender_path.txt")
    try:
        with open(path_file, 'w') as f:
            f.write(blender_path)
    except:
        pass


def find_blender():
    """Find Blender installation automatically."""
    # First check saved path
    saved = load_saved_blender_path()
    if saved:
        return saved
    
    # Then check environment variable
    env_blender = os.environ.get('BLENDER')
    if env_blender and os.path.exists(env_blender):
        return env_blender
    
    # Platform-specific paths
    if sys.platform == 'darwin':  # macOS
        paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
            "/opt/homebrew/bin/blender",
            "/usr/local/bin/blender",
        ]
    elif sys.platform == 'win32':  # Windows
        paths = []
        # Check all versions 4.5 down to 3.0
        for major in [4, 3]:
            for minor in range(9, -1, -1):
                version = f"{major}.{minor}"
                paths.append(rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe")
        
        # Generic paths
        paths.extend([
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
            r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
            os.path.expanduser(r"~\Blender\blender.exe"),
        ])
    else:  # Linux
        paths = [
            "/usr/bin/blender",
            "/snap/bin/blender",
            "/usr/local/bin/blender",
        ]
        # Home directory versions
        for major in [4, 3]:
            for minor in range(9, -1, -1):
                version = f"{major}.{minor}"
                paths.append(os.path.expanduser(f"~/blender-{version}/blender"))
        paths.append(os.path.expanduser("~/blender/blender"))
        # Steam
        paths.append(os.path.expanduser("~/.steam/steam/steamapps/common/Blender/blender"))
    
    for p in paths:
        if os.path.exists(p):
            return p
    return ""


class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    finished = Signal(bool, str)
    progress = Signal(str)


class ProcessWorker(threading.Thread):
    """Background worker for running Blender processing."""
    
    def __init__(self, blender_path, input_file, script_dir, skip_learning=False):
        super().__init__()
        self.blender_path = blender_path
        self.input_file = input_file
        self.script_dir = script_dir
        self.skip_learning = skip_learning
        self.signals = WorkerSignals()
        self.daemon = True
    
    def run(self):
        script_path = os.path.join(self.script_dir, "bounding_box_minimizer.py")
        
        if not os.path.exists(script_path):
            self.signals.finished.emit(False, 
                f"Script not found!\n\n{script_path}\n\n"
                "Make sure bounding_box_minimizer.py is in the same folder.")
            return
        
        cmd = [
            self.blender_path,
            "--background",
            "--python", script_path,
            "--",
            self.input_file
        ]
        
        # Always skip ground detection (not needed for bounding box optimization)
        cmd.append("--no-ground")
        
        if self.skip_learning:
            cmd.append("--no-learning")
        
        try:
            self.signals.progress.emit("Running Blender...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=self.script_dir
            )
            
            if result.returncode == 0:
                input_dir = Path(self.input_file).parent
                self.signals.finished.emit(True,
                    f"Processing complete!\n\nOutput saved to:\n{input_dir}")
            else:
                error = result.stderr or result.stdout or "Unknown error"
                self.signals.finished.emit(False, f"Processing failed:\n{error[:500]}")
                
        except Exception as e:
            self.signals.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OA - Orientation Automator (Alpha)")
        self.setMinimumSize(550, 420)
        self.resize(650, 520)  # Default size, freely resizable
        self.worker = None
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Set up the UI
        self.setup_ui()
        
        # Auto-find Blender
        blender = find_blender()
        if blender:
            self.blender_input.setText(blender)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: none;
                margin-top: 8px;
                padding: 0px;
                padding-top: 24px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0;
                color: #0078d4;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 12px;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
            QCheckBox {
                spacing: 8px;
                color: #cccccc;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QProgressBar {
                background-color: #3c3c3c;
                border: none;
                border-radius: 3px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
    
    def setup_ui(self):
        """Create the user interface."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("OA - Orientation Automator")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Minimize 3D object bounding boxes automatically")
        subtitle.setStyleSheet("font-size: 12px; color: #888888;")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(10)
        
        # === Blender Installation ===
        blender_group = QGroupBox("Blender Installation")
        blender_layout = QHBoxLayout(blender_group)
        blender_layout.setContentsMargins(0, 8, 0, 0)
        blender_layout.setSpacing(12)
        
        self.blender_input = QLineEdit()
        self.blender_input.setPlaceholderText("Path to Blender executable...")
        self.blender_input.setMinimumHeight(36)
        blender_layout.addWidget(self.blender_input, stretch=1)
        
        blender_btn = QPushButton("Browse...")
        blender_btn.setMinimumHeight(36)
        blender_btn.setCursor(Qt.PointingHandCursor)
        blender_btn.clicked.connect(self.browse_blender)
        blender_layout.addWidget(blender_btn)
        
        main_layout.addWidget(blender_group)
        
        # === Input 3D Model ===
        input_group = QGroupBox("Input 3D Model")
        input_layout = QHBoxLayout(input_group)
        input_layout.setContentsMargins(0, 8, 0, 0)
        input_layout.setSpacing(12)
        
        self.input_file = QLineEdit()
        self.input_file.setPlaceholderText("Select .obj, .fbx, .ply, .blend file...")
        self.input_file.setMinimumHeight(36)
        input_layout.addWidget(self.input_file, stretch=1)
        
        input_btn = QPushButton("Browse...")
        input_btn.setMinimumHeight(36)
        input_btn.setCursor(Qt.PointingHandCursor)
        input_btn.clicked.connect(self.browse_input)
        input_layout.addWidget(input_btn)
        
        main_layout.addWidget(input_group)
        
        # === Options ===
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(0, 8, 0, 0)
        options_layout.setSpacing(10)
        
        self.skip_learning = QCheckBox("Skip using learned rotations (still records new ones)")
        self.skip_learning.setChecked(False)
        self.skip_learning.setCursor(Qt.PointingHandCursor)
        self.skip_learning.setMinimumHeight(24)
        options_layout.addWidget(self.skip_learning)
        
        # Reset learning button
        reset_row = QHBoxLayout()
        reset_row.setContentsMargins(0, 5, 0, 0)
        
        self.reset_learning_btn = QPushButton("Reset Learning Data")
        self.reset_learning_btn.setCursor(Qt.PointingHandCursor)
        self.reset_learning_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #cccccc;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                color: #ffffff;
            }
        """)
        self.reset_learning_btn.clicked.connect(self.reset_learning)
        reset_row.addWidget(self.reset_learning_btn)
        reset_row.addStretch()
        options_layout.addLayout(reset_row)
        
        main_layout.addWidget(options_group)
        
        main_layout.addSpacing(15)
        
        # === Process Button ===
        self.process_btn = QPushButton("▶  Process")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.setCursor(Qt.PointingHandCursor)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a86d9;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        self.process_btn.clicked.connect(self.process)
        main_layout.addWidget(self.process_btn)
        
        # === Progress Bar ===
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.hide()
        main_layout.addWidget(self.progress)
        
        # === Status Label ===
        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #888888; font-size: 12px;")
        main_layout.addWidget(self.status)
        
        main_layout.addStretch()
    
    @Slot()
    def browse_blender(self):
        """Open file dialog to select Blender."""
        if sys.platform == 'darwin':
            # On Mac, let user select the .app bundle or executable
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Blender",
                "/Applications",
                "All Files (*)"
            )
            if path and path.endswith('.app'):
                # Convert .app to actual executable
                path = os.path.join(path, "Contents/MacOS/Blender")
        elif sys.platform == 'win32':
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Blender",
                "C:/Program Files/Blender Foundation",
                "Executable (*.exe);;All Files (*)"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Blender",
                "/usr/bin",
                "All Files (*)"
            )
        
        if path:
            self.blender_input.setText(path)
            save_blender_path(path)
    
    @Slot()
    def browse_input(self):
        """Open file dialog to select input 3D model."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model",
            "",
            "3D Models (*.obj *.fbx *.ply *.blend *.gltf *.glb);;All Files (*)"
        )
        if path:
            self.input_file.setText(path)
    
    @Slot()
    def process(self):
        """Start processing the 3D model."""
        blender = self.blender_input.text().strip()
        input_file = self.input_file.text().strip()
        
        # Validate inputs
        if not blender:
            QMessageBox.warning(self, "Error", 
                "Please select Blender executable.\n\n"
                "Click 'Browse...' to locate blender.exe")
            return
        
        if not os.path.exists(blender):
            QMessageBox.warning(self, "Error", 
                f"Blender not found at:\n{blender}\n\n"
                "Please select a valid Blender executable.")
            return
        
        if not input_file:
            QMessageBox.warning(self, "Error", 
                "Please select an input 3D model file.\n\n"
                "Supported formats: .obj, .fbx, .ply, .blend, .gltf, .glb")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "Error", 
                f"Input file not found:\n{input_file}")
            return
        
        # Save blender path for next time
        save_blender_path(blender)
        
        # Disable UI during processing
        self.process_btn.setEnabled(False)
        self.progress.show()
        self.status.setText("Processing...")
        self.status.setStyleSheet("color: #0078d4;")
        
        # Start worker thread
        script_dir = get_app_dir()
        self.worker = ProcessWorker(
            blender, input_file, script_dir, 
            self.skip_learning.isChecked()
        )
        self.worker.signals.finished.connect(self.on_finished)
        self.worker.signals.progress.connect(self.on_progress)
        self.worker.start()
    
    @Slot(str)
    def on_progress(self, message):
        """Handle progress updates from worker."""
        self.status.setText(message)
    
    @Slot()
    def reset_learning(self):
        """Reset/clear the learned rotations."""
        reply = QMessageBox.question(
            self, 
            "Reset Learning Data",
            "This will clear all learned rotations.\n\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear the rotation_presets.json file
            presets_file = os.path.join(get_app_dir(), "rotation_presets.json")
            try:
                with open(presets_file, 'w', encoding='utf-8') as f:
                    f.write('{"rotations": {}, "patterns": {}, "statistics": {}}')
                self.status.setText("Learning data reset")
                self.status.setStyleSheet("color: #888888;")
                QMessageBox.information(self, "Reset Complete", "Learning data has been cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset learning data:\n{e}")
    
    @Slot(bool, str)
    def on_finished(self, success, message):
        """Handle worker completion."""
        self.progress.hide()
        self.process_btn.setEnabled(True)
        
        if success:
            self.status.setText("✓ Complete!")
            self.status.setStyleSheet("color: #4ec94e;")
            QMessageBox.information(self, "Success", message)
        else:
            self.status.setText("✗ Failed")
            self.status.setStyleSheet("color: #f14c4c;")
            QMessageBox.critical(self, "Error", message)


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
