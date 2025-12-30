"""
OA - Orientation Automator (Alpha) - GUI Entry Point
Refactored version with modular architecture.

⚠️ LICENSE REQUIRED - No access without valid license.
"""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from src.gui.license_dialog import LicenseDialog
from src.gui.main_window import MainWindow
from src.licensing import LicenseStorage, LicenseValidator


def main():
    """Main entry point for GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # ========================================
    # LICENSE GATE - MANDATORY
    # ========================================
    
    # First, check if a valid license already exists
    storage = LicenseStorage()
    has_existing_license = False
    
    if storage.is_activated():
        # Verify the existing license is still valid
        validator = LicenseValidator()
        license_key = storage.get_license_key()
        is_valid, message, _ = validator.check_license(license_key)
        
        if is_valid:
            has_existing_license = True
            print(f"✅ Valid license found - launching application...")
        else:
            # Clear invalid license
            storage.clear_license()
            print(f"⚠️ Existing license is invalid - showing license dialog...")
    
    # Only show license dialog if no valid license exists
    if not has_existing_license:
        license_dialog = LicenseDialog()
        result = license_dialog.exec()
        
        # If dialog was rejected (Exit clicked or closed), quit immediately
        if result != QMessageBox.Accepted:
            return 0
        
        # Verify license is activated - HARD REQUIREMENT
        if not license_dialog.is_activated():
            QMessageBox.critical(
                None,
                "License Required",
                "❌ A valid license is required to use this application.\n\n"
                "Please activate your license or purchase one to continue."
            )
            return 1
    
    # ========================================
    # License valid - proceed to main window
    # ========================================
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

