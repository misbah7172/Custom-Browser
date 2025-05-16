from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

def apply_styles(window):
    """Apply styles to the browser window and its components"""
    
    # Set the stylesheet for the entire application
    stylesheet = """
    QMainWindow {
        background-color: #f8f9fa;
    }
    
    QTabWidget::pane {
        border: 1px solid #dee2e6;
        border-radius: 6px;
        background-color: #ffffff;
    }
    
    QTabBar::tab {
        background-color: #e9ecef;
        color: #495057;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #0d6efd;
        border-bottom-color: #ffffff;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #dee2e6;
    }
    
    QPushButton {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 6px;
        margin: 2px;
    }
    
    QPushButton:hover {
        background-color: #e9ecef;
    }
    
    QPushButton:pressed {
        background-color: #dee2e6;
    }
    
    QPushButton:disabled {
        background-color: #f8f9fa;
        color: #adb5bd;
    }
    
    QLineEdit {
        padding: 8px 10px;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        background-color: #ffffff;
        selection-background-color: #0d6efd;
    }
    
    QLineEdit:focus {
        border: 1px solid #0d6efd;
    }
    
    /* Status bar styling */
    QStatusBar {
        background-color: #f8f9fa;
        color: #495057;
        border-top: 1px solid #dee2e6;
    }
    """
    
    window.setStyleSheet(stylesheet)
