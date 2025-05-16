from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QShortcut, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.navigation import NavigationBar
from ui.address_bar import AddressBar
from ui.styles import apply_styles
from ui.browser_tabs import BrowserTabs

class Browser(QMainWindow):
    """Main browser window class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Browser")
        self.setMinimumSize(1000, 600)
        
        # Setup the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        # Setup the browser tabs
        self.tabs = BrowserTabs(self)
        
        # Create the navigation controls
        self.nav_bar = NavigationBar(self)
        
        # Create the address bar
        self.address_bar = AddressBar(self)
        
        # Create the browser top bar
        self.browser_top_bar = QHBoxLayout()
        self.browser_top_bar.addWidget(self.nav_bar)
        self.browser_top_bar.addWidget(self.address_bar)
        
        # Add the top bar and tabs to the main layout
        self.layout.addLayout(self.browser_top_bar)
        self.layout.addWidget(self.tabs)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Set up the browser styles
        apply_styles(self)
        
        # Navigate to the default page (Google)
        self.tabs.add_new_tab()
        self.navigate_to_url("https://www.google.com")
        
    def navigate_to_url(self, url_string):
        """Navigate the current tab to the specified URL"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            # If URL doesn't start with a scheme, add http://
            if not url_string.startswith(('http://', 'https://')):
                url_string = 'http://' + url_string
                
            # Update the address bar text
            self.address_bar.setText(url_string)
            
            # Navigate to the URL
            url = QUrl(url_string)
            if url.isValid():
                current_tab.load(url)
            else:
                # Show error message for invalid URL
                QMessageBox.warning(
                    self, "Invalid URL", 
                    "The URL you entered is not valid. Please check and try again."
                )
    
    def update_address_bar(self, url):
        """Update the address bar with the current URL"""
        if url.toString() != "about:blank":
            self.address_bar.setText(url.toString())
            self.address_bar.setCursorPosition(0)
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on current tab"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            self.nav_bar.back_button.setEnabled(current_tab.history().canGoBack())
            self.nav_bar.forward_button.setEnabled(current_tab.history().canGoForward())

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the browser"""
        # Navigation shortcuts
        QShortcut(QKeySequence.Back, self, self.nav_bar.navigate_back)
        QShortcut(QKeySequence.Forward, self, self.nav_bar.navigate_forward)
        QShortcut(QKeySequence.Refresh, self, self.nav_bar.refresh_page)
        
        # Tab shortcuts
        QShortcut(QKeySequence.AddTab, self, self.tabs.add_new_tab)
        QShortcut(QKeySequence.Close, self, self.tabs.close_current_tab)
        
        # Focus address bar
        QShortcut(QKeySequence("Ctrl+L"), self, self.address_bar.setFocus)
