"""
OA - Orientation Automator (Alpha) - GUI Entry Point
Refactored version with modular architecture.

⚠️ LICENSE REQUIRED - No access without valid license.
"""
import sys
import os
import time
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer

from src.gui.splash_screen import SplashScreen
from src.gui.license_dialog import LicenseDialog
from src.gui.main_window import MainWindow
from src.licensing import LicenseStorage, LicenseValidator
from src.utils.paths import get_app_dir
from src.security.error_handler import setup_global_error_handler


def setup_logging():
    """Setup application-wide logging."""
    log_dir = get_app_dir()
    log_file = os.path.join(log_dir, "processing_log.txt")
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Setup global error handler with log file
    setup_global_error_handler(log_file)
    
    return log_file


def initialize_app(splash, app):
    """
    Initialize application with progress updates during startup.
    
    Args:
        splash: SplashScreen instance for progress updates
        app: QApplication instance
    
    Returns:
        tuple: (has_existing_license, window_or_dialog, main_window)
    """
    # Step 1: Load configuration and modules
    splash.set_progress(10, "Loading application modules...")
    app.processEvents()
    time.sleep(0.05)
    
    splash.set_progress(20, "Initializing configuration...")
    app.processEvents()
    time.sleep(0.05)
    
    # Step 2: Check for existing license (fast local check)
    splash.set_progress(30, "Checking license status...")
    app.processEvents()
    storage = LicenseStorage()
    has_existing_license = False
    main_window = None
    
    if storage.is_activated():
        splash.set_progress(50, "Validating license...")
        app.processEvents()
        
        # Verify the existing license is still valid
        validator = LicenseValidator()
        license_key = storage.get_license_key()
        
        splash.set_progress(70, "Connecting to license server...")
        app.processEvents()
        
        is_valid, message, _ = validator.check_license(license_key)
        
        if is_valid:
            has_existing_license = True
            splash.set_progress(85, "License verified - loading application...")
            app.processEvents()
            time.sleep(0.1)
            
            # Initialize main window
            splash.set_progress(90, "Preparing user interface...")
            app.processEvents()
            main_window = MainWindow()
            
            splash.set_progress(100, "Ready!")
            app.processEvents()
            time.sleep(0.2)
            
            return (True, None, main_window)
        else:
            # Clear invalid license
            storage.clear_license()
            splash.set_progress(60, "License validation failed...")
            app.processEvents()
            time.sleep(0.1)
    
    # Step 3: Prepare license dialog if needed
    if not has_existing_license:
        splash.set_progress(70, "Preparing license activation...")
        app.processEvents()
        time.sleep(0.05)
        
        splash.set_progress(85, "Loading license dialog...")
        app.processEvents()
        license_dialog = LicenseDialog()
        
        splash.set_progress(100, "Ready!")
        app.processEvents()
        time.sleep(0.2)
        
        return (False, license_dialog, None)
    
    return (True, None, main_window)


def main():
    """Main entry point for GUI application."""
    # Setup logging FIRST (before anything else that might error)
    log_file = None
    try:
        log_file = setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("="*60)
        logger.info("OA - Orientation Automator starting...")
        logger.info(f"Log file: {log_file}")
    except Exception as e:
        # Fallback: at least try to log to a known location
        fallback_log = os.path.join(os.getcwd(), "processing_log.txt")
        try:
            with open(fallback_log, 'a', encoding='utf-8') as f:
                f.write(f"\n[ERROR] Failed to setup logging: {e}\n")
            log_file = fallback_log
        except:
            pass  # Can't even write to fallback log
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # ========================================
    # SHOW LOADING SCREEN
    # ========================================
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # ========================================
    # INITIALIZE WITH PROGRESS UPDATES
    # ========================================
    try:
        has_existing_license, dialog_or_none, main_window = initialize_app(splash, app)
        
        # ========================================
    # LICENSE GATE - MANDATORY
    # ========================================
        
        if has_existing_license and main_window:
            # License valid - close splash and show main window
            splash.close()
            app.processEvents()
            main_window.show()
            sys.exit(app.exec())
        
        elif not has_existing_license and dialog_or_none:
            # No license - close splash and show license dialog
            splash.close()
            app.processEvents()
            
            result = dialog_or_none.exec()
            
            # If dialog was rejected (Exit clicked or closed), quit immediately
            if result != QMessageBox.Accepted:
                return 0
            
            # Verify license is activated - HARD REQUIREMENT
            if not dialog_or_none.is_activated():
                QMessageBox.critical(
                    None,
                    "License Required",
                    "❌ A valid license is required to use this application.\n\n"
                    "Please activate your license or purchase one to continue."
                )
                return 1
            
            # License activated - show main window
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
        
        else:
            # Unexpected state
            splash.close()
            QMessageBox.critical(
                None,
                "Startup Error",
                "An unexpected error occurred during startup."
            )
            return 1
        
    except Exception as e:
        splash.set_progress(100, f"Error: {str(e)}")
        app.processEvents()
        QTimer.singleShot(2000, splash.close)
        
        # Show error with log file location
        log_location = log_file if log_file else os.path.join(get_app_dir(), "processing_log.txt")
        error_msg = (
            f"An error occurred during startup:\n\n{str(e)}\n\n"
            f"Log file location:\n{log_location}\n\n"
            f"Please check the log file for details."
        )
        QMessageBox.critical(
            None,
            "Startup Error",
            error_msg
        )
        return 1


if __name__ == "__main__":
    main()

