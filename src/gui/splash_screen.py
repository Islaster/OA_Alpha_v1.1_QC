"""
Loading splash screen with progress updates.
Shows during app initialization.
"""
from PySide6.QtWidgets import (
    QSplashScreen, QApplication, QLabel, QVBoxLayout, QWidget, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QFont, QPainter, QColor


class ProgressUpdater(QObject):
    """Signal emitter for progress updates."""
    progress = Signal(int, str)  # percentage, message
    finished = Signal()


class SplashScreen(QSplashScreen):
    """
    Startup loading screen with progress bar and status messages.
    Shows during application initialization.
    """
    
    def __init__(self, pixmap=None):
        """Initialize splash screen."""
        if pixmap is None:
            # Create a professional startup splash screen
            pixmap = QPixmap(500, 350)
            pixmap.fill(QColor(30, 30, 30))  # Dark background
            
            # Draw logo/text with better styling
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Title
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(28)
            font.setBold(True)
            painter.setFont(font)
            title_rect = pixmap.rect()
            title_rect.setBottom(title_rect.height() // 2 - 40)
            painter.drawText(
                title_rect,
                Qt.AlignCenter,
                "OA - Orientation Automator"
            )
            
            # Subtitle
            font.setPointSize(12)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor(180, 180, 180))
            subtitle_rect = pixmap.rect()
            subtitle_rect.setTop(title_rect.bottom() + 10)
            subtitle_rect.setBottom(subtitle_rect.top() + 30)
            painter.drawText(
                subtitle_rect,
                Qt.AlignCenter,
                "Version 1.1.0 - Professional Edition"
            )
            
            painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.SplashScreen | 
            Qt.FramelessWindowHint
        )
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        splash_rect = self.geometry()
        self.move(
            (screen.width() - splash_rect.width()) // 2,
            (screen.height() - splash_rect.height()) // 2
        )
        
        # Progress updater
        self.progress_updater = ProgressUpdater()
        self.progress_updater.progress.connect(self.update_progress)
        
        # Current progress
        self.current_progress = 0
        self.current_message = "Starting application..."
        
        # Draw initial progress
        self.draw_progress()
    
    def draw_progress(self):
        """Draw progress bar and message on splash screen."""
        pixmap = self.pixmap()
        if pixmap is None:
            return
        
        # Create a copy to draw on
        splash_pixmap = pixmap.copy()
        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw progress bar background
        bar_rect = splash_pixmap.rect()
        bar_rect.setTop(bar_rect.bottom() - 80)
        bar_rect.setLeft(20)
        bar_rect.setRight(bar_rect.right() - 20)
        
        # Background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRoundedRect(bar_rect, 5, 5)
        
        # Progress fill
        if self.current_progress > 0:
            fill_rect = bar_rect
            fill_rect.setWidth(int(fill_rect.width() * self.current_progress / 100))
            painter.setBrush(QColor(0, 120, 215))  # Blue progress
            painter.drawRoundedRect(fill_rect, 5, 5)
        
        # Progress text
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Percentage
        percent_text = f"{self.current_progress}%"
        percent_rect = bar_rect
        percent_rect.setBottom(percent_rect.top() + 25)
        painter.drawText(percent_rect, Qt.AlignCenter, percent_text)
        
        # Status message
        message_rect = bar_rect
        message_rect.setTop(message_rect.top() + 30)
        painter.setPen(QColor(200, 200, 200))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(message_rect, Qt.AlignCenter, self.current_message)
        
        painter.end()
        self.setPixmap(splash_pixmap)
    
    def update_progress(self, percentage: int, message: str):
        """Update progress bar and message."""
        self.current_progress = min(100, max(0, percentage))
        self.current_message = message
        self.draw_progress()
        QApplication.processEvents()  # Update UI immediately
    
    def set_progress(self, percentage: int, message: str = ""):
        """Set progress (convenience method)."""
        self.update_progress(percentage, message)
    
    def finish_splash(self, window):
        """Finish splash screen and show main window."""
        if window:
            window.show()
        self.close()
    
    def close_splash(self):
        """Close the splash screen."""
        self.close()


def show_loading_screen(app, init_function, *args, **kwargs):
    """
    Show loading screen while executing initialization function.
    
    Args:
        app: QApplication instance
        init_function: Function to execute during loading
        *args, **kwargs: Arguments to pass to init_function
    
    Returns:
        Result of init_function
    """
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    try:
        # Update progress during initialization
        splash.set_progress(10, "Loading application...")
        app.processEvents()
        
        # Call initialization function with progress callback
        result = init_function(splash, *args, **kwargs)
        
        # Complete
        splash.set_progress(100, "Ready!")
        app.processEvents()
        
        # Show for a brief moment
        QTimer.singleShot(300, splash.close)
        app.processEvents()
        
        return result
    except Exception as e:
        splash.set_progress(100, f"Error: {str(e)}")
        app.processEvents()
        QTimer.singleShot(2000, splash.close)
        raise

