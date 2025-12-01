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
        /* Windows-specific font size adjustments */
        * {
            font-size: 9pt;
        }
        
        QPushButton {
            padding: 3px 8px;
            min-height: 20px;
            font-size: 9pt;
        }
        
        /* Fix GroupBox excessive top padding and title styling on Windows */
        QGroupBox {
            padding-top: 10px;
            margin-top: 0px;
            font-size: 9pt;
            border: 1px solid #11356B;
            border-radius: 5px;
        }
        
        QGroupBox::title {
            subcontrol-origin: border;
            subcontrol-position: top left;
            padding: 4px;
            margin: 0px;
            background-color: #11356B;
            color: white;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 9pt;
            min-width: 148px;
        }
        
        /* Target specific GroupBox widths */
        QGroupBox#groupBox_2::title,
        QGroupBox#groupBox_3::title,
        QGroupBox#groupBox_4::title {
            min-width: 148px;
        }
        
        QGroupBox#groupBox_5::title {
            min-width: 148px;
        }
        
        QGroupBox#groupBox::title {
            min-width: 128px;
        }
        
        QSpinBox, QDoubleSpinBox {
            padding: 2px;
            min-height: 20px;
            font-size: 9pt;
        }
        
        QTabBar::tab {
            padding: 6px 10px;
            min-width: 50px;
            font-size: 9pt;
        }
        
        QLabel {
            font-size: 9pt;
        }
        
        QTableView {
            font-size: 9pt;
        }
        
        QCheckBox {
            font-size: 9pt;
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
