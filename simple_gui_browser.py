#!/usr/bin/env python3
"""
Simplified GUI browser with tracking and security features
- Works even without QtWebEngine
- Tracks URL visits
- Logs IP addresses
- Tracks geolocation
- Implements personal firewall
"""
import sys
import os
import socket
from urllib.parse import urlparse

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QDialog, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QTextEdit
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction

# Database Manager
from db_manager import DatabaseManager

class SimpleBrowserTab(QWidget):
    """Simple browser tab that doesn't require WebEngine"""
    
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self._url = QUrl()
        self._title = "New Tab"
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # URL display
        self.url_label = QLabel("Current URL:")
        layout.addWidget(self.url_label)
        
        # Content display
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        layout.addWidget(self.content)
        
        # Status display
        self.status = QLabel("Ready")
        layout.addWidget(self.status)
    
    def load(self, url):
        """Load a URL"""
        self._url = url
        url_str = url.toString()
        self.url_label.setText(f"URL: {url_str}")
        
        # Update browser's address bar
        if self.browser:
            if hasattr(self.browser, 'update_address_bar'):
                self.browser.update_address_bar(url)
            
            # Check if site is blocked
            if url_str != "about:blank" and hasattr(self.browser, 'db_manager'):
                if self.browser.db_manager.is_domain_blocked(url_str):
                    self.content.setPlainText("⛔ This website has been blocked by firewall settings.")
                    self.status.setText("Blocked by firewall")
                    return
        
        # Try to fetch basic content
        try:
            parsed_url = urlparse(url_str)
            domain = parsed_url.netloc
            
            if domain:
                # Get IP address
                try:
                    ip_address = socket.gethostbyname(domain)
                    self.status.setText(f"Connected to: {domain} ({ip_address})")
                    
                    # Show basic content (simple version)
                    self.content.setPlainText(f"Connected to {domain}\nIP Address: {ip_address}\n\nContent would appear here in a real browser.")
                    
                    # Update title
                    self._title = domain
                    
                except socket.gaierror:
                    self.content.setPlainText(f"Could not resolve domain: {domain}")
                    self.status.setText("Domain resolution failed")
            else:
                self.content.setPlainText("Please enter a valid URL")
                self.status.setText("No domain specified")
        
        except Exception as e:
            self.content.setPlainText(f"Error loading page: {str(e)}")
            self.status.setText("Error")
    
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
    
    def reload(self):
        """Reload the current page"""
        self.load(self._url)

class BrowserTabs(QTabWidget):
    """Tab widget for browser tabs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Tab settings
        self.setTabsClosable(True)
        self.setMovable(True)
        
        # Add new tab button
        new_tab_button = QPushButton("+")
        new_tab_button.setFixedSize(24, 24)
        new_tab_button.clicked.connect(self.add_new_tab)
        self.setCornerWidget(new_tab_button, Qt.Corner.TopRightCorner)
        
        # Connect signals
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_change)
    
    def add_new_tab(self, qurl=None):
        """Add a new browser tab"""
        if qurl is None:
            qurl = QUrl("https://www.google.com")
        
        # Create tab
        tab = SimpleBrowserTab(self.browser)
        index = self.addTab(tab, "New Tab")
        self.setCurrentIndex(index)
        
        # Load URL
        tab.load(qurl)
        self.setTabText(index, tab.title())
        
        return tab
    
    def close_tab(self, index):
        """Close a tab"""
        if self.count() > 1:
            widget = self.widget(index)
            self.removeTab(index)
            if widget:
                widget.deleteLater()
        else:
            self.currentWidget().load(QUrl("https://www.google.com"))
    
    def close_current_tab(self):
        """Close the current tab"""
        self.close_tab(self.currentIndex())
    
    def on_tab_change(self, index):
        """Handle tab change"""
        if index >= 0 and hasattr(self.browser, 'update_address_bar'):
            current_tab = self.currentWidget()
            if current_tab:
                self.browser.update_address_bar(current_tab.url())

class AddressBar(QLineEdit):
    """Address bar for entering URLs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setPlaceholderText("Enter URL or search terms...")
        self.returnPressed.connect(self.navigate_to_url)
    
    def navigate_to_url(self):
        """Navigate to the URL in the address bar"""
        url_text = self.text().strip()
        
        if not url_text:
            return
        
        # Check if it's a search
        if ' ' in url_text or '.' not in url_text:
            search_url = f"https://www.google.com/search?q={url_text.replace(' ', '+')}"
            self.browser.navigate_to_url(search_url)
        else:
            self.browser.navigate_to_url(url_text)

class NavigationBar(QWidget):
    """Navigation bar with back/forward/refresh buttons"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Navigation buttons
        self.back_button = QPushButton("◀")
        self.back_button.setFixedSize(30, 30)
        self.back_button.setToolTip("Back")
        self.back_button.clicked.connect(self.navigate_back)
        
        self.forward_button = QPushButton("▶")
        self.forward_button.setFixedSize(30, 30)
        self.forward_button.setToolTip("Forward")
        self.forward_button.clicked.connect(self.navigate_forward)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.clicked.connect(self.refresh_page)
        
        # Add buttons to layout
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.refresh_button)
        
        # Disable buttons initially
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
    
    def navigate_back(self):
        """Go back in history"""
        pass  # Simplified browser doesn't support history
    
    def navigate_forward(self):
        """Go forward in history"""
        pass  # Simplified browser doesn't support history
    
    def refresh_page(self):
        """Refresh the current page"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.reload()

class FirewallDialog(QDialog):
    """Dialog for managing the firewall blocklist"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # Setup dialog
        self.setWindowTitle("Firewall Settings")
        self.setMinimumSize(500, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel("Website Firewall")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("Block malicious websites by domain name")
        layout.addWidget(desc)
        
        # Domain input
        domain_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Enter domain to block (e.g., example.com)")
        block_button = QPushButton("Block Domain")
        block_button.clicked.connect(self.block_domain)
        domain_layout.addWidget(self.domain_input)
        domain_layout.addWidget(block_button)
        layout.addLayout(domain_layout)
        
        # Blocked domains list
        layout.addWidget(QLabel("Blocked Domains:"))
        self.blocked_list = QListWidget()
        self.blocked_list.setAlternatingRowColors(True)
        layout.addWidget(self.blocked_list)
        
        # Unblock button
        unblock_button = QPushButton("Unblock Selected")
        unblock_button.clicked.connect(self.unblock_selected)
        layout.addWidget(unblock_button)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load blocked domains
        self.update_blocked_list()
    
    def update_blocked_list(self):
        """Update the list of blocked domains"""
        self.blocked_list.clear()
        for domain in self.db_manager.get_blocked_domains():
            item = QListWidgetItem(domain)
            self.blocked_list.addItem(item)
    
    def block_domain(self):
        """Block a domain"""
        domain = self.domain_input.text().strip()
        
        if not domain:
            return
        
        # Format domain
        if "://" in domain:
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        if not domain:
            QMessageBox.warning(self, "Invalid Domain", "Please enter a valid domain name.")
            return
        
        # Block domain
        if self.db_manager.block_domain(domain):
            self.domain_input.clear()
            self.update_blocked_list()
            QMessageBox.information(self, "Domain Blocked", f"The domain '{domain}' has been blocked.")
    
    def unblock_selected(self):
        """Unblock a domain"""
        selected = self.blocked_list.selectedItems()
        if not selected:
            return
        
        domain = selected[0].text()
        if self.db_manager.unblock_domain(domain):
            self.update_blocked_list()
            QMessageBox.information(self, "Domain Unblocked", f"The domain '{domain}' has been unblocked.")

class VisitHistoryDialog(QDialog):
    """Dialog for viewing browsing history"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # Setup dialog
        self.setWindowTitle("Visit History")
        self.setMinimumSize(700, 500)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel("Website Visit History")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("All visited websites with their IP addresses and locations")
        layout.addWidget(desc)
        
        # Visit list
        self.visit_list = QListWidget()
        self.visit_list.setAlternatingRowColors(True)
        layout.addWidget(self.visit_list)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load visits
        self.load_visits()
    
    def load_visits(self):
        """Load visit history"""
        visits = self.db_manager.get_recent_visits()
        
        for visit in visits:
            url = visit['url']
            title = visit['title'] or url
            ip = visit['ip_address']
            location = visit['location']
            timestamp = visit['visit_time']
            
            text = f"{title} - {ip} - {location} - {timestamp}"
            item = QListWidgetItem(text)
            item.setToolTip(url)
            self.visit_list.addItem(item)

class SimpleBrowser(QMainWindow):
    """Simple browser with tracking and security features"""
    
    def __init__(self):
        super().__init__()
        
        # Setup window
        self.setWindowTitle("Simple Browser with Tracking & Security")
        self.setMinimumSize(1000, 600)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        # Create tabs first
        self.tabs = BrowserTabs(self)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create navigation bar
        self.nav_bar = NavigationBar(self)
        
        # Create address bar
        self.address_bar = AddressBar(self)
        
        # Top bar layout
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.nav_bar)
        top_bar.addWidget(self.address_bar)
        
        # Add components to main layout
        self.layout.addLayout(top_bar)
        self.layout.addWidget(self.tabs)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Apply styling
        self.apply_styles()
        
        # Create first tab
        self.tabs.add_new_tab(QUrl("https://www.google.com"))
    
    def create_menu_bar(self):
        """Create menu bar"""
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
        
        # Firewall action
        firewall_action = QAction("Firewall Settings", self)
        firewall_action.triggered.connect(self.show_firewall)
        security_menu.addAction(firewall_action)
        
        # History action
        history_action = QAction("Visit History & Tracking", self)
        history_action.triggered.connect(self.show_visit_history)
        security_menu.addAction(history_action)
    
    def navigate_to_url(self, url_string):
        """Navigate to a URL"""
        if not url_string.startswith(('http://', 'https://')):
            url_string = 'http://' + url_string
        
        # Check if domain is blocked
        if self.db_manager.is_domain_blocked(url_string):
            QMessageBox.warning(
                self, "Blocked Website", 
                "This website has been blocked by the firewall settings."
            )
            return
        
        # Update address bar
        self.address_bar.setText(url_string)
        
        # Navigate to URL
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.load(QUrl(url_string))
    
    def update_address_bar(self, url):
        """Update address bar with current URL"""
        url_string = url.toString()
        if url_string != "about:blank":
            self.address_bar.setText(url_string)
            
            # Track visit
            current_tab = self.tabs.currentWidget()
            if current_tab:
                title = current_tab.title()
                self.db_manager.add_visit(url_string, title)
                
                # Update status bar
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
                    print(f"Error: {e}")
    
    def show_firewall(self):
        """Show firewall settings"""
        dialog = FirewallDialog(self.db_manager, self)
        dialog.exec()
    
    def show_visit_history(self):
        """Show visit history"""
        dialog = VisitHistoryDialog(self.db_manager, self)
        dialog.exec()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Address bar focus
        address_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_shortcut.activated.connect(self.address_bar.setFocus)
        
        # Refresh
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.nav_bar.refresh_page)
    
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
    browser = SimpleBrowser()
    browser.show()
    sys.exit(app.exec())