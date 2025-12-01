"""Platform-specific styling adjustments for cross-platform PyQt6 GUI compatibility."""
import sys
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def get_platform_scale_factor():
    """Get platform-specific scale factor for fonts and sizes."""
    system = platform.system()
    if system == "Windows":
        return 1.0
    elif system == "Darwin":  # macOS
        return 1.0
    else:  # Linux
        return 1.0


def apply_platform_specific_styles(app: QApplication):
    """Apply platform-specific high DPI settings."""
    system = platform.system()
    
    if system == "Windows":
        # Enable high DPI scaling for Windows
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )


def get_platform_stylesheet_adjustments():
    """Get platform-specific stylesheet adjustments."""
    system = platform.system()
    
    adjustments = ""
    
    if system == "Windows":
        # Windows-specific adjustments
        adjustments = """
        /* Windows-specific padding adjustments */
        QPushButton {
            padding: 3px 8px;
            min-height: 20px;
        }
        
        QGroupBox {
            padding-top: 20px;
            margin-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            left: 10px;
        }
        
        QSpinBox, QDoubleSpinBox {
            padding: 2px;
            min-height: 20px;
        }
        
        QTabBar::tab {
            padding: 6px 10px;
            min-width: 50px;
        }
        
        QSlider::groove:horizontal {
            height: 6px;
        }
        
        QSlider::handle:horizontal {
            width: 14px;
            margin: -5px 0;
        }
        """
    
    return adjustments
