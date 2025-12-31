"""
Main GUI window for OA - Orientation Automator.
"""
import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QProgressBar, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, Slot

from .blender_finder import find_blender, save_blender_path
from .theme import get_dark_theme_stylesheet, get_button_style_secondary, get_button_style_primary
from .workers import ProcessWorker
from src.utils.paths import get_app_dir


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("OA - Orientation Automator (Alpha)")
        self.setMinimumSize(550, 420)
        self.resize(650, 520)
        self.worker = None
        
        # Apply dark theme
        self.setStyleSheet(get_dark_theme_stylesheet())
        
        # Set up the UI
        self.setup_ui()
        
        # Auto-find Blender
        blender = find_blender()
        if blender:
            self.blender_input.setText(blender)
    
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
        
        self.input_browse_btn = QPushButton("Browse...")
        self.input_browse_btn.setMinimumHeight(36)
        self.input_browse_btn.setCursor(Qt.PointingHandCursor)
        self.input_browse_btn.clicked.connect(self.browse_input)
        input_layout.addWidget(self.input_browse_btn)
        
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
        self.reset_learning_btn.setStyleSheet(get_button_style_secondary())
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
        self.process_btn.setStyleSheet(get_button_style_primary())
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
        try:
            if sys.platform == 'darwin':
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Blender",
                    "/Applications",
                    "All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog  # Use Qt dialog to avoid macOS issues
                )
                if path and path.endswith('.app'):
                    # Convert .app to actual executable
                    path = os.path.join(path, "Contents/MacOS/Blender")
            elif sys.platform == 'win32':
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Blender",
                    "C:/Program Files/Blender Foundation",
                    "Executable (*.exe);;All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog
                )
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Select Blender",
                    "/usr/bin",
                    "All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog
                )
            
            if path:
                self.blender_input.setText(path)
                save_blender_path(path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open file dialog:\n{str(e)}"
            )
    
    @Slot()
    def browse_input(self):
        """Open file dialog to select input 3D model."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Disable the button to prevent multiple clicks
        self.input_browse_btn.setEnabled(False)
        
        try:
            # Set a reasonable starting directory (user's home or Downloads)
            # Use try/except to avoid blocking on slow filesystems
            start_dir = ""
            try:
                downloads = os.path.expanduser("~/Downloads")
                if os.path.exists(downloads):
                    start_dir = downloads
                else:
                    start_dir = os.path.expanduser("~")
            except Exception:
                # Fallback to current directory if home expansion fails
                start_dir = os.getcwd()
            
            logger.debug(f"Opening file dialog with start_dir: {start_dir}")
            
            # Use exec() instead of getOpenFileName for better control
            # This ensures the dialog is modal and blocks properly
            dialog = QFileDialog(self, "Select 3D Model", start_dir)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setNameFilter("3D Models (*.obj *.fbx *.ply *.blend *.gltf *.glb);;All Files (*)")
            dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
            dialog.setOption(QFileDialog.Option.DontResolveSymlinks, True)  # Faster on macOS
            
            if dialog.exec() == QFileDialog.DialogCode.Accepted:
                files = dialog.selectedFiles()
                if files:
                    path = files[0]
                    self.input_file.setText(path)
                    logger.debug(f"Selected file: {path}")
        except Exception as e:
            logger.error(f"Error in browse_input: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open file dialog:\n{str(e)}"
            )
        finally:
            # Always re-enable the button
            self.input_browse_btn.setEnabled(True)
    
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

