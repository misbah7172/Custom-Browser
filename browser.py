from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QTabWidget, QMenuBar, QMenu,
    QStatusBar
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.navigation import NavigationBar
from ui.address_bar import AddressBar
from ui.styles import apply_styles
from ui.browser_tabs import BrowserTabs
from ui.firewall import FirewallManager, VisitHistoryDialog
from db_manager import DatabaseManager

class Browser(QMainWindow):
    """Main browser window class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Browser")
        self.setMinimumSize(1000, 600)
        
        # Initialize database manager for tracking and firewall
        self.db_manager = DatabaseManager()
        
        # Setup the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # Setup menu bar
        self.setup_menu_bar()
        
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
        self.main_layout.addLayout(self.browser_top_bar)
        self.main_layout.addWidget(self.tabs)
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Set up the browser styles
        apply_styles(self)
        
        # Navigate to the default page (Google)
        self.tabs.add_new_tab()
        self.navigate_to_url("https://www.google.com")
    
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
        
        # Tools menu
        tools_menu = QMenu("Tools", self)
        menu_bar.addMenu(tools_menu)
        
        # Firewall settings
        firewall_action = QAction("Firewall Settings", self)
        firewall_action.triggered.connect(self.show_firewall_settings)
        tools_menu.addAction(firewall_action)
        
        # Visit history
        history_action = QAction("Visit History", self)
        history_action.triggered.connect(self.show_visit_history)
        tools_menu.addAction(history_action)
        
    def navigate_to_url(self, url_string):
        """Navigate the current tab to the specified URL"""
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
        """Update the address bar with the current URL"""
        url_string = url.toString()
        if url_string != "about:blank":
            self.address_bar.setText(url_string)
            self.address_bar.setCursorPosition(0)
            
            # Record this visit in the database
            current_tab = self.tabs.currentWidget()
            if current_tab:
                title = current_tab.title()
                self.db_manager.add_visit(url_string, title)
                
                # Update status bar with IP info
                try:
                    import socket
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url_string)
                    if parsed_url.netloc:
                        try:
                            ip = socket.gethostbyname(parsed_url.netloc)
                            self.status_bar.showMessage(f"Connected to: {parsed_url.netloc} ({ip})")
                        except:
                            self.status_bar.showMessage(f"Connected to: {parsed_url.netloc}")
                except:
                    pass
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on current tab"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            self.nav_bar.back_button.setEnabled(current_tab.history().canGoBack())
            self.nav_bar.forward_button.setEnabled(current_tab.history().canGoForward())

    def show_firewall_settings(self):
        """Open the firewall settings dialog"""
        firewall_manager = FirewallManager(self.db_manager)
        firewall_manager.domain_blocked.connect(self.on_domain_blocked)
        firewall_manager.domain_unblocked.connect(self.on_domain_unblocked)
        firewall_manager.setWindowTitle("Firewall Settings")
        firewall_manager.setMinimumSize(500, 400)
        firewall_manager.show()  # Using show() instead of exec() for non-modal behavior
    
    def on_domain_blocked(self, domain):
        """Handle when a domain is blocked"""
        self.status_bar.showMessage(f"Domain blocked: {domain}", 3000)
    
    def on_domain_unblocked(self, domain):
        """Handle when a domain is unblocked"""
        self.status_bar.showMessage(f"Domain unblocked: {domain}", 3000)
    
    def show_visit_history(self):
        """Show the visit history dialog"""
        history_dialog = VisitHistoryDialog(self.db_manager, self)
        history_dialog.exec()

    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the browser"""
        # Navigation shortcuts - Use string-based shortcuts instead of QKeySequence attributes
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self.nav_bar.navigate_back)
        
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self.nav_bar.navigate_forward)
        
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.nav_bar.refresh_page)
        
        # Tab shortcuts
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.tabs.add_new_tab)
        
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.tabs.close_current_tab)
        
        # Focus address bar
        focus_address_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_address_shortcut.activated.connect(self.address_bar.setFocus)
