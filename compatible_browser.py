#!/usr/bin/env python3
"""
Modern GUI web browser with tracking and security features
Compatible with PyQt6 installation in virtual environments
"""
import sys
import os
import socket
from urllib.parse import urlparse

# Qt Imports - with proper compatibility checks
from PyQt6.QtCore import QUrl, Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QDialog, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction

# Check if WebEngine is available
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6 import QtWebEngineCore
    WEBENGINE_AVAILABLE = True
except ImportError:
    print("QtWebEngine not available. Using basic browser instead.")
    WEBENGINE_AVAILABLE = False

# Database Manager
from db_manager import DatabaseManager

class SimpleWebView(QWidget):
    """Fallback when QWebEngineView is not available"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Message label
        self.message = QLabel("WebEngine not available. Using simplified view.")
        self.layout.addWidget(self.message)
        
        # URL display
        self.url_label = QLabel("Current URL:")
        self.layout.addWidget(self.url_label)
        
        # Content area
        self.content = QLabel("Content would appear here")
        self.content.setWordWrap(True)
        self.content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ddd;")
        self.layout.addWidget(self.content)
        
        self._url = QUrl()
        self._title = "New Tab"
    
    def load(self, url):
        """Simulate loading a URL"""
        self._url = url
        self.url_label.setText(f"Current URL: {url.toString()}")
        self.content.setText(f"Simulated content for {url.toString()}")
        # Signal that we would emit if we were a real WebEngineView
        if hasattr(self, 'urlChanged'):
            self.urlChanged.emit(url)
        if hasattr(self, 'loadFinished'):
            self.loadFinished.emit(True)
    
    def url(self):
        """Return the current URL"""
        return self._url
    
    def title(self):
        """Return the page title"""
        return self._title
    
    def history(self):
        """Simulate a history object"""
        class SimpleHistory:
            def canGoBack(self):
                return False
            def canGoForward(self):
                return False
        return SimpleHistory()
    
    def back(self):
        """Simulate going back"""
        print("Cannot go back in simplified view")
    
    def forward(self):
        """Simulate going forward"""
        print("Cannot go forward in simplified view")
    
    def reload(self):
        """Simulate reload"""
        self.load(self._url)

# Use the real QWebEngineView if available, otherwise use our simple version
WebView = QWebEngineView if WEBENGINE_AVAILABLE else SimpleWebView

# If WebEngine is available, create a proper web view
if WEBENGINE_AVAILABLE:
    class EnhancedWebView(QWebEngineView):
        """Enhanced web view with additional functionality"""
        
        def __init__(self, browser, tab_widget):
            super().__init__()
            self.browser = browser
            self.tab_widget = tab_widget
            
            # Connect signals to browser methods
            self.urlChanged.connect(self.browser.update_address_bar)
            self.loadFinished.connect(self.browser.update_navigation_buttons)
        
        def createWindow(self, window_type):
            """Handle creating a new window from the web page"""
            new_tab = EnhancedWebView(self.browser, self.tab_widget)
            self.tab_widget.add_view_in_new_tab(new_tab)
            return new_tab
else:
    # Fallback with our simple web view
    class EnhancedWebView(SimpleWebView):
        """Enhanced simple web view with additional functionality"""
        
        def __init__(self, browser, tab_widget):
            super().__init__()
            self.browser = browser
            self.tab_widget = tab_widget
            
            # Add signals that QWebEngineView would have
            self.urlChanged = pyqtSignal(QUrl)
            self.loadFinished = pyqtSignal(bool)
            self.titleChanged = pyqtSignal(str)
            
            # Connect signals to browser methods
            self.urlChanged.connect(self.browser.update_address_bar)
            self.loadFinished.connect(self.browser.update_navigation_buttons)
        
        def createWindow(self, window_type):
            """Handle creating a new window from the web page"""
            new_tab = EnhancedWebView(self.browser, self.tab_widget)
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
        web_view = EnhancedWebView(self.browser, self)
        web_view.load(qurl)
        
        # Add to tabs
        index = self.addTab(web_view, "New Tab")
        self.setCurrentIndex(index)
        
        # Update title when page title changes
        if hasattr(web_view, 'titleChanged'):
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
        if hasattr(web_view, 'titleChanged'):
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

class AddressBar(QLineEdit):
    """Address bar for entering and displaying URLs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Set placeholder text
        self.setPlaceholderText("Enter URL or search terms...")
        
        # Connect to returnPressed signal for URL navigation
        self.returnPressed.connect(self.navigate_to_url)
        
        # Set initial size policy
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.setMinimumHeight(30)
    
    def navigate_to_url(self):
        """Navigate to the URL entered in the address bar"""
        url_text = self.text().strip()
        
        # If empty, do nothing
        if not url_text:
            return
        
        # Check if input looks like a search query
        if " " in url_text or "." not in url_text:
            # Format as a Google search
            search_url = f"https://www.google.com/search?q={url_text.replace(' ', '+')}"
            self.browser.navigate_to_url(search_url)
        else:
            # Navigate directly to the URL
            self.browser.navigate_to_url(url_text)
    
    def keyPressEvent(self, event):
        """Handle additional keyboard events for the address bar"""
        # Escape key clears focus
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        # Default handling for other keys
        else:
            super().keyPressEvent(event)

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
        self.back_button.setText("◀")
        self.back_button.clicked.connect(self.navigate_back)
        
        # Forward button
        self.forward_button = QPushButton()
        self.forward_button.setToolTip("Go Forward")
        self.forward_button.setFixedSize(30, 30)
        self.forward_button.setText("▶")
        self.forward_button.clicked.connect(self.navigate_forward)
        
        # Refresh button
        self.refresh_button = QPushButton()
        self.refresh_button.setToolTip("Refresh Page")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setText("⟳")
        self.refresh_button.clicked.connect(self.refresh_page)
        
        # Add buttons to layout
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.refresh_button)
        
        # Initialize button states
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
    
    def navigate_back(self):
        """Navigate back in the current tab's history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'history'):
            if hasattr(current_tab.history(), 'canGoBack') and current_tab.history().canGoBack():
                current_tab.back()
    
    def navigate_forward(self):
        """Navigate forward in the current tab's history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'history'):
            if hasattr(current_tab.history(), 'canGoForward') and current_tab.history().canGoForward():
                current_tab.forward()
    
    def refresh_page(self):
        """Refresh the current tab"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'reload'):
            current_tab.reload()

class FirewallDialog(QDialog):
    """Dialog for managing the firewall blocklist"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.setWindowTitle("Firewall Settings")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Website Firewall")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Description
        description = QLabel("Block malicious websites by domain name")
        layout.addWidget(description)
        
        # Block domain input
        domain_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Enter domain to block (e.g., example.com)")
        block_button = QPushButton("Block Domain")
        block_button.clicked.connect(self.block_domain)
        domain_layout.addWidget(self.domain_input)
        domain_layout.addWidget(block_button)
        layout.addLayout(domain_layout)
        
        # List of blocked domains
        layout.addWidget(QLabel("Blocked Domains:"))
        self.blocked_list = QListWidget()
        self.blocked_list.setAlternatingRowColors(True)
        layout.addWidget(self.blocked_list)
        
        # Unblock button
        unblock_button = QPushButton("Unblock Selected")
        unblock_button.clicked.connect(self.unblock_selected)
        layout.addWidget(unblock_button)
        
        # Load blocked domains
        self.update_blocked_list()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def update_blocked_list(self):
        """Update the list of blocked domains"""
        self.blocked_list.clear()
        for domain in self.db_manager.get_blocked_domains():
            item = QListWidgetItem(domain)
            self.blocked_list.addItem(item)
    
    def block_domain(self):
        """Block a domain entered by the user"""
        domain = self.domain_input.text().strip()
        
        # Validate domain
        if not domain:
            return
        
        # Remove protocol if present
        if "://" in domain:
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Block domain in database
        if self.db_manager.block_domain(domain):
            self.domain_input.clear()
            self.update_blocked_list()
            QMessageBox.information(self, "Domain Blocked", f"The domain '{domain}' has been blocked.")
    
    def unblock_selected(self):
        """Unblock the selected domain"""
        selected_items = self.blocked_list.selectedItems()
        if not selected_items:
            return
        
        domain = selected_items[0].text()
        if self.db_manager.unblock_domain(domain):
            self.update_blocked_list()
            QMessageBox.information(self, "Domain Unblocked", f"The domain '{domain}' has been unblocked.")

class VisitHistoryDialog(QDialog):
    """Dialog showing history of visited sites with their details"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.setWindowTitle("Website Visit History")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Recent Website Visits")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Description
        description = QLabel("All visited websites with their IP addresses and locations")
        layout.addWidget(description)
        
        # Visit list
        self.visit_list = QListWidget()
        self.visit_list.setAlternatingRowColors(True)
        layout.addWidget(self.visit_list)
        
        # Load visits
        self.load_visits()
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_visits(self):
        """Load and display visit history"""
        visits = self.db_manager.get_recent_visits()
        
        for visit in visits:
            url = visit['url']
            title = visit['title'] or url
            ip = visit['ip_address']
            location = visit['location']
            timestamp = visit['visit_time']
            
            display_text = f"{title} - {ip} - {location} - {timestamp}"
            item = QListWidgetItem(display_text)
            item.setToolTip(url)
            self.visit_list.addItem(item)

class ModernBrowser(QMainWindow):
    """Main browser window with tracking and security features"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Browser with Tracking & Security")
        self.setMinimumSize(1000, 600)
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Setup central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # Setup tabs first (needed for menu bar actions)
        self.tabs = BrowserTabs(self)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Navigation controls
        self.nav_bar = NavigationBar(self)
        
        # Address bar
        self.address_bar = AddressBar(self)
        
        # Top bar layout
        self.browser_top_bar = QHBoxLayout()
        self.browser_top_bar.addWidget(self.nav_bar)
        self.browser_top_bar.addWidget(self.address_bar)
        
        # Add components to main layout
        self.main_layout.addLayout(self.browser_top_bar)
        self.main_layout.addWidget(self.tabs)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Apply styles
        self.apply_styles()
        
        # Open default page
        self.tabs.add_new_tab()
        self.navigate_to_url("https://www.google.com")
        
        # Show WebEngine availability status
        if not WEBENGINE_AVAILABLE:
            self.status_bar.showMessage("QtWebEngine not available. Using simplified browser mode.")
            QMessageBox.warning(
                self, 
                "Limited Functionality", 
                "QtWebEngine not available. Browser is running in simplified mode with limited functionality.\n\n"
                "All tracking and security features are still functional."
            )
    
    def setup_menu_bar(self):
        """Create the menu bar with various options"""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)
        
        # New tab action
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.tabs.add_new_tab)
        file_menu.addAction(new_tab_action)
        
        # Close tab action
        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.tabs.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Security menu
        security_menu = QMenu("Security", self)
        menu_bar.addMenu(security_menu)
        
        # Firewall settings
        firewall_action = QAction("Firewall Settings", self)
        firewall_action.triggered.connect(self.show_firewall)
        security_menu.addAction(firewall_action)
        
        # Visit history with tracking
        history_action = QAction("Visit History & Tracking", self)
        history_action.triggered.connect(self.show_visit_history)
        security_menu.addAction(history_action)
    
    def navigate_to_url(self, url_string):
        """Navigate to the specified URL with security checks"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            # If URL doesn't start with a scheme, add http://
            if not url_string.startswith(('http://', 'https://')):
                url_string = 'http://' + url_string
                
            # Update the address bar text
            self.address_bar.setText(url_string)
            
            # Check if the domain is blocked by firewall
            if self.db_manager.is_domain_blocked(url_string):
                QMessageBox.warning(
                    self, "Blocked Website", 
                    "This website has been blocked by the firewall settings."
                )
                return
            
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
        """Update the address bar and track the visit"""
        url_string = url.toString()
        if url_string != "about:blank":
            self.address_bar.setText(url_string)
            self.address_bar.setCursorPosition(0)
            
            # Record this visit in the database
            current_tab = self.tabs.currentWidget()
            if current_tab:
                title = current_tab.title() if hasattr(current_tab, 'title') else url_string
                self.db_manager.add_visit(url_string, title)
                
                # Update status bar with IP info
                try:
                    parsed_url = urlparse(url_string)
                    domain = parsed_url.netloc
                    if domain:
                        try:
                            ip = socket.gethostbyname(domain)
                            self.status_bar.showMessage(f"Connected to: {domain} ({ip})")
                        except:
                            self.status_bar.showMessage(f"Connected to: {domain}")
                except Exception as e:
                    print(f"Error resolving IP: {e}")
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'history'):
            history = current_tab.history()
            if hasattr(history, 'canGoBack'):
                self.nav_bar.back_button.setEnabled(history.canGoBack())
            if hasattr(history, 'canGoForward'):
                self.nav_bar.forward_button.setEnabled(history.canGoForward())
    
    def show_firewall(self):
        """Show the firewall management dialog"""
        firewall_dialog = FirewallDialog(self.db_manager, self)
        firewall_dialog.exec()
    
    def show_visit_history(self):
        """Show the visit history dialog"""
        history_dialog = VisitHistoryDialog(self.db_manager, self)
        history_dialog.exec()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self.nav_bar.navigate_back)
        
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self.nav_bar.navigate_forward)
        
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.nav_bar.refresh_page)
        
        # Address bar focus
        address_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_shortcut.activated.connect(self.address_bar.setFocus)
    
    def apply_styles(self):
        """Apply styling to the browser"""
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
        
        QLineEdit {
            padding: 8px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: #ffffff;
        }
        
        QLineEdit:focus {
            border: 1px solid #0d6efd;
        }
        
        QStatusBar {
            background-color: #f8f9fa;
            color: #495057;
            border-top: 1px solid #dee2e6;
        }
        """
        
        self.setStyleSheet(stylesheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Modern Browser")
    app.setOrganizationName("ModernBrowser")
    
    browser = ModernBrowser()
    browser.show()
    
    sys.exit(app.exec())