from PyQt6.QtWidgets import QTabWidget, QPushButton, QTabBar
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

class WebEngineView(QWebEngineView):
    """Extended QWebEngineView with additional functionality"""
    
    def __init__(self, browser, tab_widget):
        super().__init__()
        self.browser = browser
        self.tab_widget = tab_widget
        
        # Connect signals to browser methods
        self.urlChanged.connect(self.browser.update_address_bar)
        self.loadFinished.connect(self.browser.update_navigation_buttons)
        
        # Set page settings
        self.page().settings().setAttribute(
            QWebEnginePage.WebAttribute.JavascriptCanOpenWindows, True
        )
        self.page().settings().setAttribute(
            QWebEnginePage.WebAttribute.LocalStorageEnabled, True
        )

    def createWindow(self, window_type):
        """Handle creating a new window from the web page (e.g. popup)"""
        # Create a new tab for the requested window
        new_tab = WebEngineView(self.browser, self.tab_widget)
        self.tab_widget.add_view_in_new_tab(new_tab)
        return new_tab

class BrowserTabs(QTabWidget):
    """Tab widget to hold multiple browser tabs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Tab settings
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        
        # Configure "+" tab
        self.setCornerWidget(self.create_new_tab_button(), Qt.Corner.TopRightCorner)
        
        # Connect signals
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_change)
    
    def create_new_tab_button(self):
        """Create a button for adding new tabs"""
        new_tab_button = QPushButton("+")
        new_tab_button.setFixedSize(24, 24)
        new_tab_button.setToolTip("Open a new tab")
        new_tab_button.clicked.connect(self.add_new_tab)
        return new_tab_button
    
    def add_new_tab(self, qurl=None):
        """Add a new browser tab"""
        if qurl is None:
            qurl = QUrl("https://www.google.com")
        
        # Create web view for the new tab
        web_view = WebEngineView(self.browser, self)
        web_view.load(qurl)
        
        # Add to tabs
        index = self.addTab(web_view, "New Tab")
        self.setCurrentIndex(index)
        
        # Update title when page title changes
        web_view.titleChanged.connect(
            lambda title, view=web_view: self.update_tab_title(view, title)
        )
        
        # Set focus to the web view
        web_view.setFocus()
        
        return web_view
    
    def add_view_in_new_tab(self, web_view):
        """Add an existing web view in a new tab"""
        # Add to tabs
        index = self.addTab(web_view, "New Tab")
        self.setCurrentIndex(index)
        
        # Update title when page title changes
        web_view.titleChanged.connect(
            lambda title, view=web_view: self.update_tab_title(view, title)
        )
        
        return web_view
    
    def update_tab_title(self, view, title):
        """Update the tab title for the given view"""
        index = self.indexOf(view)
        if index != -1:
            # Truncate long titles
            if len(title) > 20:
                title = title[:17] + "..."
            self.setTabText(index, title)
    
    def close_tab(self, index):
        """Close the tab at the given index"""
        # Don't close the last tab
        if self.count() > 1:
            # Get the widget at this index
            widget = self.widget(index)
            
            # Remove the tab
            self.removeTab(index)
            
            # Delete the widget to free resources
            if widget:
                widget.deleteLater()
        else:
            # If it's the last tab, just clear it and go to Google
            self.currentWidget().load(QUrl("https://www.google.com"))
    
    def close_current_tab(self):
        """Close the currently active tab"""
        current_index = self.currentIndex()
        self.close_tab(current_index)
    
    def on_tab_change(self, index):
        """Handle tab change events"""
        if index >= 0:
            # Update browser's address bar and navigation buttons
            current_url = self.currentWidget().url()
            self.browser.update_address_bar(current_url)
            self.browser.update_navigation_buttons()
