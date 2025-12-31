"""
License activation dialog for OA - Orientation Automator.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QTextBrowser
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QPixmap
import os

from src.licensing import LicenseValidator, LicenseStorage


class LicenseDialog(QDialog):
    """
    Dialog for license activation.
    Shows on first run or when no valid license is found.
    """
    
    def __init__(self, parent=None, error_message=None, prefill_key=None):
        """
        Initialize license dialog.
        
        Args:
            parent: Parent widget
            error_message: Optional error message to display
            prefill_key: Optional license key to prefill in the input field
        """
        super().__init__(parent)
        self.storage = LicenseStorage()
        self.validator = LicenseValidator()
        self.is_licensed = False
        self.error_message = error_message
        self.prefill_key = prefill_key
        
        self.setWindowTitle("OA - License Activation")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.check_existing_license()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        # Load and scale icon to match emoji size (~24px for 18pt font)
        # Try multiple possible paths (development vs compiled)
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icon.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "icon.png"),
            "assets/icon.png",
            os.path.join(os.getcwd(), "assets", "icon.png"),
        ]
        
        icon_loaded = False
        for icon_path in possible_paths:
            if os.path.exists(icon_path):
                try:
                    icon_pixmap = QPixmap(icon_path)
                    if not icon_pixmap.isNull():
                        # Scale to ~24px height to match emoji size (18pt font ≈ 24px emoji)
                        icon_pixmap = icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        icon_label = QLabel()
                        icon_label.setPixmap(icon_pixmap)
                        title_layout.addWidget(icon_label)
                        title_layout.addSpacing(8)  # Small spacing between icon and text
                        icon_loaded = True
                        break
                except Exception as e:
                    # Silently continue to next path if icon loading fails
                    # This is expected behavior - we have multiple fallback paths
                    continue
        
        # Fallback to emoji if icon not found
        if not icon_loaded:
            icon_label = QLabel("🎯")
            icon_label.setFont(QFont("", 18))  # Match font size
            title_layout.addWidget(icon_label)
            title_layout.addSpacing(8)
        
        title_text = QLabel("OA - Orientation Automator")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_text.setFont(title_font)
        title_layout.addWidget(title_text)
        
        layout.addLayout(title_layout)
        
        # Version info
        version_label = QLabel("Version 1.1.0 - Professional Edition")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(10)
        
        # Info box
        info_box = QTextBrowser()
        info_box.setMaximumHeight(120)
        info_box.setOpenExternalLinks(True)
        info_box.setHtml("""
            <div style='font-size: 11pt; line-height: 1.5;'>
                <p><b>🔑 License Required</b></p>
                <p>A valid license key is required to use this application.</p>
                <p style='margin-top: 10px;'>
                    <a href='https://gruntwave.lemonsqueezy.com/checkout/buy/45184e99-9c63-414d-bca1-e5f8b4063c4e' style='color: #4CAF50; text-decoration: none; font-weight: bold;'>Purchase a License →</a>
                </p>
            </div>
        """)
        layout.addWidget(info_box)
        
        layout.addSpacing(10)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        # License key input
        key_layout = QVBoxLayout()
        key_label = QLabel("License Key:")
        key_layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your license key...")
        self.key_input.setMinimumHeight(35)
        self.key_input.setFocus()  # Set focus to input field
        key_layout.addWidget(self.key_input)
        
        layout.addLayout(key_layout)
        
        # Device info
        device_label = QLabel(f"This device: {self.validator.machine_id}")
        device_label.setStyleSheet("color: gray; font-size: 9pt;")
        device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.reject)
        self.exit_button.setMinimumHeight(40)
        
        self.activate_button = QPushButton("Activate License")
        self.activate_button.clicked.connect(self.activate_license)
        self.activate_button.setDefault(True)
        self.activate_button.setMinimumHeight(40)
        self.activate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        button_layout.addWidget(self.exit_button)
        button_layout.addWidget(self.activate_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def check_existing_license(self):
        """
        Check if a valid license already exists.
        
        Note: This should only be called if gui_new.py didn't find a valid license.
        This is a fallback check for edge cases.
        """
        # If error message provided, show it
        if self.error_message:
            self.status_label.setText(f"❌ License Validation Failed: {self.error_message}")
            self.status_label.setStyleSheet("""
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            """)
            # Prefill the old key if provided, or clear it
            if self.prefill_key:
                self.key_input.setText(self.prefill_key)
                # Select the text so user can easily replace it
                self.key_input.selectAll()
            else:
                self.key_input.clear()
            self.key_input.setEnabled(True)
            self.key_input.setFocus()
            self.activate_button.setEnabled(True)
        elif self.storage.is_activated():
            license_key = self.storage.get_license_key()
            
            # Quick validation
            is_valid, message, _ = self.validator.check_license(license_key)
            
            if is_valid:
                # This shouldn't normally happen if gui_new.py did its check
                self.show_licensed_status()
                self.is_licensed = True
                self.accept()
            else:
                self.show_unlicensed_status()
                self.storage.clear_license()  # Clear invalid license
                # Prefill the old key so user can try a new one
                if license_key:
                    self.key_input.setText(license_key)
                    self.key_input.selectAll()
        else:
            # No existing license - ensure input is ready
            self.key_input.setEnabled(True)
            self.key_input.setFocus()
            self.activate_button.setEnabled(True)
            # Prefill key if provided
            if self.prefill_key:
                self.key_input.setText(self.prefill_key)
                self.key_input.selectAll()
    
    def show_licensed_status(self):
        """Show licensed status."""
        self.status_label.setText("✅ Licensed - Full Version")
        self.status_label.setStyleSheet("""
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        self.key_input.setEnabled(False)
        self.activate_button.setEnabled(False)
        self.exit_button.setText("Continue")
    
    def show_unlicensed_status(self):
        """Show unlicensed status."""
        self.status_label.setText("❌ No License - Activation Required")
        self.status_label.setStyleSheet("""
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        # Make sure input is enabled
        self.key_input.setEnabled(True)
        self.key_input.setFocus()
        self.activate_button.setEnabled(True)
    
    def activate_license(self):
        """Activate the entered license key."""
        license_key = self.key_input.text().strip()
        
        if not license_key:
            QMessageBox.warning(
                self,
                "No License Key",
                "Please enter a license key."
            )
            return
        
        # Show progress
        self.activate_button.setEnabled(False)
        self.activate_button.setText("Activating...")
        
        # Validate and activate
        is_valid, message, data = self.validator.check_license(license_key)
        
        if is_valid:
            # Save license
            instance_id = data.get("instance_id")
            if instance_id:
                self.storage.save_license(
                    license_key=license_key,
                    instance_id=instance_id,
                    instance_name=self.validator.machine_id
                )
            
            self.is_licensed = True
            self.show_licensed_status()
            
            QMessageBox.information(
                self,
                "Activation Successful",
                f"✅ License activated successfully!\n\n"
                f"You now have access to all professional features.\n\n"
                f"Device: {self.validator.machine_id}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Activation Failed",
                f"❌ Could not activate license.\n\n"
                f"Reason: {message}\n\n"
                f"Please check your license key and try again."
            )
            self.activate_button.setEnabled(True)
            self.activate_button.setText("Activate License")
    
    def is_activated(self) -> bool:
        """Check if license is activated."""
        return self.is_licensed


class LicenseChecker:
    """
    Simple utility to check license status without showing dialog.
    """
    
    @staticmethod
    def has_valid_license() -> bool:
        """
        Check if user has a valid license.
        
        Returns:
            bool: True if licensed, False if not
        """
        storage = LicenseStorage()
        return storage.is_activated()
    
    @staticmethod
    def get_license_status() -> str:
        """
        Get license status string.
        
        Returns:
            str: "Licensed" or "Unlicensed"
        """
        return "Licensed" if LicenseChecker.has_valid_license() else "Unlicensed"
    
    @staticmethod
    def show_purchase_dialog(parent=None):
        """Show information about purchasing a license."""
        msg = QMessageBox(parent)
        msg.setWindowTitle("Purchase License")
        msg.setText("🔑 License Required\n\n"
                   "A valid license is required to use this application.\n\n"
                   "Features included:\n"
                   "• Advanced bounding box optimization\n"
                   "• Multiple file format support\n"
                   "• Learning system\n"
                   "• Priority support")
        msg.setInformativeText("Click 'Open Store' to purchase a license.")
        msg.addButton("Open Store", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        
        result = msg.exec()
        if result == QMessageBox.AcceptRole:
            QDesktopServices.openUrl(QUrl("https://gruntwave.lemonsqueezy.com/checkout/buy/45184e99-9c63-414d-bca1-e5f8b4063c4e"))

