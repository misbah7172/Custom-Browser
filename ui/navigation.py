from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtSvg import QSvgRenderer

class NavigationBar(QWidget):
    """Navigation bar with back, forward, and refresh buttons"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setMaximumHeight(40)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Back button
        self.back_button = QPushButton()
        self.back_button.setToolTip("Go Back")
        self.back_button.setFixedSize(30, 30)
        self.back_button.setIcon(self.text_icon("◀"))
        self.back_button.clicked.connect(self.navigate_back)
        
        # Forward button
        self.forward_button = QPushButton()
        self.forward_button.setToolTip("Go Forward")
        self.forward_button.setFixedSize(30, 30)
        self.forward_button.setIcon(self.text_icon("▶"))
        self.forward_button.clicked.connect(self.navigate_forward)
        
        # Refresh button
        self.refresh_button = QPushButton()
        self.refresh_button.setToolTip("Refresh Page")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setIcon(self.text_icon("⟳"))
        self.refresh_button.clicked.connect(self.refresh_page)
        
        # Add buttons to layout
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.refresh_button)
        
        # Initialize button states
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
    
    def text_icon(self, text):
        """Create a text-based icon since we can't use image files"""
        # This is a simple way to create icons without external files
        class TextIcon(QIcon):
            def __init__(self, text):
                super().__init__()
                self.text = text
            
            def paint(self, painter, rect, mode=QIcon.Mode.Normal, state=QIcon.State.Off):
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text)
        
        return TextIcon(text)
    
    def navigate_back(self):
        """Navigate back in the current tab's history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab and current_tab.history().canGoBack():
            current_tab.back()
    
    def navigate_forward(self):
        """Navigate forward in the current tab's history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab and current_tab.history().canGoForward():
            current_tab.forward()
    
    def refresh_page(self):
        """Refresh the current tab"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.reload()
