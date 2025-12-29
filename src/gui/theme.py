"""
GUI theme and styling.
"""


def get_dark_theme_stylesheet():
    """
    Get dark theme stylesheet for Qt application.
    
    Returns:
        CSS stylesheet string
    """
    return """
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
    """


def get_button_style_secondary():
    """Get secondary button style (for reset/utility buttons)."""
    return """
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
    """


def get_button_style_primary():
    """Get primary button style (for main action button)."""
    return """
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
    """

