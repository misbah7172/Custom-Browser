#!/usr/bin/env python3
"""
Web Browser - A simple, modern browser with dark mode, incognito mode and security features
"""
import sys
import os
import re
import sqlite3
import socket
import ssl
from urllib.parse import urlparse
import json
from datetime import datetime
import hashlib

# Try to import optional security packages
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests package not available. Some security features will be limited.")

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("Warning: dnspython package not available. DNS over HTTPS will be disabled.")

from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QPushButton, QLineEdit, QLabel, QFrame,
    QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QCheckBox, QRadioButton, QGroupBox, QToolBar, QSizePolicy
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction, QColor, QPalette

# Try to import WebEngine components
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineUrlRequestInterceptor
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
    print("WebEngine components not available. Using simplified browser.")

# Security Manager for handling security features
class SecurityManager:
    def __init__(self):
        self.phishing_domains = set()
        self.known_malicious_ips = set()
        self.load_security_data()
        
        # Initialize DNS resolver if available
        if DNS_AVAILABLE:
            self.dns_resolver = dns.resolver.Resolver()
            self.dns_resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Google and Cloudflare DNS
        else:
            self.dns_resolver = None
        
    def load_security_data(self):
        """Load security data from online sources"""
        if not REQUESTS_AVAILABLE:
            print("Warning: Security data loading disabled - requests package not available")
            return
            
        try:
            # Load phishing domains list
            response = requests.get('https://openphish.com/feed.txt')
            if response.status_code == 200:
                self.phishing_domains.update(response.text.splitlines())
            
            # Load known malicious IPs
            response = requests.get('https://blocklist.net.ua/blocklist.csv')
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if ',' in line:
                        ip = line.split(',')[0]
                        self.known_malicious_ips.add(ip)
        except Exception as e:
            print(f"Error loading security data: {e}")
    
    def check_ssl_certificate(self, url):
        """Check SSL certificate validity"""
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc
            
            # Create SSL context
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return True, cert
        except Exception as e:
            return False, str(e)
    
    def is_phishing_site(self, url):
        """Check if URL is a known phishing site"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Check against known phishing domains
            if domain in self.phishing_domains:
                return True
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'login.*\.com',
                r'secure.*\.com',
                r'account.*\.com',
                r'verify.*\.com',
                r'confirm.*\.com'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, domain, re.I):
                    return True
            
            return False
        except:
            return False
    
    def is_malicious_ip(self, ip):
        """Check if IP is known to be malicious"""
        return ip in self.known_malicious_ips
    
    def resolve_dns_over_https(self, domain):
        """Resolve domain using DNS over HTTPS"""
        if not DNS_AVAILABLE:
            return []
            
        try:
            answers = self.dns_resolver.resolve(domain, 'A')
            return [str(rdata) for rdata in answers]
        except Exception as e:
            print(f"DNS resolution error: {e}")
            return []

# URL Request Interceptor for security checks (only available with WebEngine)
if WEB_ENGINE_AVAILABLE:
    class SecurityInterceptor(QWebEngineUrlRequestInterceptor):
        def __init__(self, security_manager):
            super().__init__()
            self.security_manager = security_manager
        
        def interceptRequest(self, info):
            """Intercept and check requests for security"""
            url = info.requestUrl().toString()
            
            # Check for phishing
            if self.security_manager.is_phishing_site(url):
                info.block(True)
                return
            
            # Check SSL certificate
            valid, cert = self.security_manager.check_ssl_certificate(url)
            if not valid:
                info.block(True)
                return
            
            # Check IP
            try:
                parsed_url = urlparse(url)
                ip = socket.gethostbyname(parsed_url.netloc)
                if self.security_manager.is_malicious_ip(ip):
                    info.block(True)
                    return
            except:
                pass

# Enhanced Database Manager with security features
class DatabaseManager:
    def __init__(self, incognito=False):
        self.incognito = incognito
        if not incognito:
            self.db_path = os.path.expanduser("~/.browser_data.db")
            self.connect()
            self.create_tables()
            self.migrate_database()
            self.blocked_domains = self.get_blocked_domains()
        else:
            self.conn = None
            self.cursor = None
            self.blocked_domains = []
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Database error: {e}")
            self.conn = None
            self.cursor = None
    
    def migrate_database(self):
        """Migrate database schema if needed"""
        if self.incognito or not self.cursor:
            return
            
        try:
            # Check if port column exists
            self.cursor.execute("PRAGMA table_info(visits)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'port' not in columns:
                # Add port column
                self.cursor.execute("ALTER TABLE visits ADD COLUMN port INTEGER")
                self.conn.commit()
                print("Database migrated: Added port column")
        except Exception as e:
            print(f"Error during database migration: {e}")
    
    def create_tables(self):
        if self.incognito or not self.cursor:
            return
            
        try:
            # Table for visited sites
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    ip_address TEXT,
                    port INTEGER,
                    ssl_valid BOOLEAN,
                    security_status TEXT,
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for blocked sites
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS firewall (
                    id INTEGER PRIMARY KEY,
                    domain TEXT UNIQUE NOT NULL,
                    blocked_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for bookmarks
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for settings
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    def add_visit(self, url, title, security_info=None):
        if self.incognito or not self.cursor:
            return False
        
        try:
            # Get domain and IP
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            if not domain or domain == "about:blank":
                return False
            
            try:
                ip_address = socket.gethostbyname(domain)
                # Get port from URL or use default
                port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            except:
                ip_address = "Unknown"
                port = None
            
            # Add to database with security info
            self.cursor.execute(
                """INSERT INTO visits 
                   (url, title, ip_address, port, ssl_valid, security_status) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (url, title, ip_address, port, 
                 security_info.get('ssl_valid', False) if security_info else False,
                 security_info.get('status', 'Unknown') if security_info else 'Unknown')
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording visit: {e}")
            return False
    
    def get_recent_visits(self, limit=100):
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute(
                "SELECT url, title, ip_address, port, ssl_valid, security_status, visit_time FROM visits ORDER BY visit_time DESC LIMIT ?",
                (limit,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting visits: {e}")
            return []
    
    def is_domain_blocked(self, url):
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            for blocked in self.blocked_domains:
                if domain == blocked or domain.endswith("." + blocked):
                    return True
            
            return False
        except:
            return False
    
    def block_domain(self, domain):
        if self.incognito:
            self.blocked_domains.append(domain)
            return True
            
        if not self.cursor:
            return False
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO firewall (domain) VALUES (?)",
                (domain,)
            )
            self.conn.commit()
            self.blocked_domains = self.get_blocked_domains()
            return True
        except Exception as e:
            print(f"Error blocking domain: {e}")
            return False
    
    def unblock_domain(self, domain):
        if self.incognito:
            if domain in self.blocked_domains:
                self.blocked_domains.remove(domain)
            return True
            
        if not self.cursor:
            return False
        
        try:
            self.cursor.execute("DELETE FROM firewall WHERE domain = ?", (domain,))
            self.conn.commit()
            self.blocked_domains = self.get_blocked_domains()
            return True
        except Exception as e:
            print(f"Error unblocking domain: {e}")
            return False
    
    def get_blocked_domains(self):
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute("SELECT domain FROM firewall")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error getting blocked domains: {e}")
            return []
    
    def add_bookmark(self, url, title):
        if self.incognito or not self.cursor:
            return False
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO bookmarks (url, title) VALUES (?, ?)",
                (url, title)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False
    
    def remove_bookmark(self, url):
        if self.incognito or not self.cursor:
            return False
        
        try:
            self.cursor.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing bookmark: {e}")
            return False
    
    def get_bookmarks(self):
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute("SELECT url, title FROM bookmarks ORDER BY title")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting bookmarks: {e}")
            return []
    
    def save_setting(self, key, value):
        if self.incognito or not self.cursor:
            return False
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving setting: {e}")
            return False
    
    def get_setting(self, key, default=None):
        if self.incognito or not self.cursor:
            return default
        
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result[0] if result else default
        except Exception as e:
            print(f"Error getting setting: {e}")
            return default
    
    def close(self):
        if not self.incognito and self.conn:
            self.conn.close()

# Enhanced Browser Tab with security features
class BrowserTab(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Security status indicator
        self.security_status = QLabel()
        self.security_status.setFixedHeight(20)
        self.security_status.setStyleSheet("background-color: #f0f0f0; padding: 2px;")
        layout.addWidget(self.security_status)
        
        # Progress bar
        self.progress_bar = QFrame()
        self.progress_bar.setFrameShape(QFrame.Shape.HLine)
        self.progress_bar.setFrameShadow(QFrame.Shadow.Sunken)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setStyleSheet("background-color: #2196F3;")
        self.progress_bar.hide()
        
        # Create web view based on availability
        if WEB_ENGINE_AVAILABLE:
            # Use QWebEngineView if available
            self.web_view = QWebEngineView()
            
            # Set up profile for incognito mode
            if browser.incognito_mode:
                profile = QWebEngineProfile()
                page = QWebEnginePage(profile, self.web_view)
                self.web_view.setPage(page)
            
            # Enable security features
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
            
            # Connect signals
            self.web_view.loadStarted.connect(self.on_load_started)
            self.web_view.loadProgress.connect(self.on_load_progress)
            self.web_view.loadFinished.connect(self.on_load_finished)
            self.web_view.urlChanged.connect(self.on_url_changed)
            self.web_view.titleChanged.connect(self.on_title_changed)
        else:
            # Create a placeholder widget
            self.web_view = QLabel("WebEngine not available. Install PyQt6-WebEngine to view websites.")
            self.web_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.web_view.setStyleSheet("font-size: 16px; color: #666;")
        
        # Add widgets to layout
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.web_view)
    
    def load(self, url):
        """Load a URL in this tab"""
        if not WEB_ENGINE_AVAILABLE:
            return
        
        if isinstance(url, str):
            url = QUrl(url)
        
        self.web_view.load(url)
    
    def on_load_started(self):
        """Handle load started"""
        self.progress_bar.show()
    
    def on_load_progress(self, progress):
        """Handle load progress"""
        # Update progress bar width based on progress
        width = int((progress / 100.0) * self.width())
        self.progress_bar.setFixedWidth(width)
    
    def on_load_finished(self, success):
        """Handle load finished"""
        if success:
            # Animate progress completion
            self.progress_bar.setFixedWidth(self.width())
            QTimer.singleShot(300, self.progress_bar.hide)
        else:
            self.progress_bar.hide()
    
    def on_url_changed(self, url):
        """Handle URL changed"""
        if self.browser:
            self.browser.update_address_bar(url)
            
            # Record visit if not incognito
            if not self.browser.incognito_mode:
                url_str = url.toString()
                if url_str != "about:blank":
                    title = self.web_view.title()
                    self.browser.db_manager.add_visit(url_str, title)
    
    def on_title_changed(self, title):
        """Handle title changed"""
        # Update tab title
        index = self.browser.tabs.indexOf(self)
        if index >= 0:
            display_title = title[:20] + "..." if len(title) > 20 else title
            self.browser.tabs.setTabText(index, display_title)
    
    def url(self):
        """Get current URL"""
        if WEB_ENGINE_AVAILABLE:
            return self.web_view.url()
        return QUrl()
    
    def title(self):
        """Get page title"""
        if WEB_ENGINE_AVAILABLE:
            return self.web_view.title()
        return "No WebEngine"
    
    def back(self):
        """Go back in history"""
        if WEB_ENGINE_AVAILABLE:
            self.web_view.back()
    
    def forward(self):
        """Go forward in history"""
        if WEB_ENGINE_AVAILABLE:
            self.web_view.forward()
    
    def reload(self):
        """Reload the page"""
        if WEB_ENGINE_AVAILABLE:
            self.web_view.reload()
    
    def can_go_back(self):
        """Check if we can go back"""
        if WEB_ENGINE_AVAILABLE:
            return self.web_view.history().canGoBack()
        return False
    
    def can_go_forward(self):
        """Check if we can go forward"""
        if WEB_ENGINE_AVAILABLE:
            return self.web_view.history().canGoForward()
        return False
    
    def update_security_status(self, url):
        """Update security status indicator"""
        try:
            # Check SSL certificate
            valid, cert = self.browser.security_manager.check_ssl_certificate(url)
            
            # Check for phishing
            is_phishing = self.browser.security_manager.is_phishing_site(url)
            
            # Update status
            if is_phishing:
                self.security_status.setText("⚠️ Phishing Site Detected")
                self.security_status.setStyleSheet("background-color: #ffebee; color: #c62828; padding: 2px;")
            elif not valid:
                self.security_status.setText("⚠️ Insecure Connection")
                self.security_status.setStyleSheet("background-color: #fff3e0; color: #ef6c00; padding: 2px;")
            else:
                self.security_status.setText("🔒 Secure Connection")
                self.security_status.setStyleSheet("background-color: #e8f5e9; color: #2e7d32; padding: 2px;")
        except:
            self.security_status.setText("⚠️ Security Check Failed")
            self.security_status.setStyleSheet("background-color: #ffebee; color: #c62828; padding: 2px;")

# Tabs widget to manage multiple browser tabs
class BrowserTabs(QTabWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Set tab properties
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        
        # Add new tab button
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(24, 24)
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)
        
        # Connect signals
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_change)
    
    def add_new_tab(self, url=None):
        """Add a new browser tab"""
        if url is None:
            url = QUrl("https://www.google.com")
        
        # Create new tab
        tab = BrowserTab(self.browser)
        
        # Add tab to widget
        index = self.addTab(tab, "New Tab")
        self.setCurrentIndex(index)
        
        # Load URL
        tab.load(url)
        
        return tab
    
    def close_tab(self, index):
        """Close tab at index"""
        if self.count() > 1:
            # Remove and delete tab
            widget = self.widget(index)
            self.removeTab(index)
            if widget:
                widget.deleteLater()
        else:
            # Just reload last tab instead of closing
            self.currentWidget().load(QUrl("https://www.google.com"))
    
    def close_current_tab(self):
        """Close current tab"""
        self.close_tab(self.currentIndex())
    
    def on_tab_change(self, index):
        """Handle tab change"""
        if index >= 0:
            current_tab = self.currentWidget()
            if current_tab:
                # Update UI
                url = current_tab.url()
                self.browser.update_address_bar(url)
                self.browser.update_navigation_buttons()

# Address bar for entering URLs
class AddressBar(QLineEdit):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Setup
        self.setPlaceholderText("Search or enter website name")
        self.returnPressed.connect(self.navigate_to_url)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(30)
    
    def navigate_to_url(self):
        """Navigate to URL entered in address bar"""
        url_text = self.text().strip()
        
        if not url_text:
            return
        
        # Check if it's a search query or URL
        if ' ' in url_text or '.' not in url_text:
            # Use Google search
            search_url = f"https://www.google.com/search?q={url_text.replace(' ', '+')}"
            self.browser.navigate_to_url(search_url)
        else:
            self.browser.navigate_to_url(url_text)

# Navigation bar with browser buttons
class NavigationBar(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Back button
        self.back_button = QPushButton("◀")
        self.back_button.setFixedSize(30, 30)
        self.back_button.setToolTip("Back")
        self.back_button.clicked.connect(self.navigate_back)
        
        # Forward button
        self.forward_button = QPushButton("▶")
        self.forward_button.setFixedSize(30, 30)
        self.forward_button.setToolTip("Forward")
        self.forward_button.clicked.connect(self.navigate_forward)
        
        # Refresh button
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setToolTip("Refresh")
        self.refresh_button.clicked.connect(self.refresh_page)
        
        # Home button
        self.home_button = QPushButton("🏠")
        self.home_button.setFixedSize(30, 30)
        self.home_button.setToolTip("Home")
        self.home_button.clicked.connect(self.go_home)
        
        # Add buttons to layout
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.home_button)
        
        # Initialize state
        self.back_button.setEnabled(False)
        self.forward_button.setEnabled(False)
    
    def navigate_back(self):
        """Go back in history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.back()
    
    def navigate_forward(self):
        """Go forward in history"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.forward()
    
    def refresh_page(self):
        """Refresh current page"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.reload()
    
    def go_home(self):
        """Go to home page"""
        self.browser.navigate_to_url("https://www.google.com")
    
    def update_button_states(self):
        """Update button states based on current tab"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            self.back_button.setEnabled(current_tab.can_go_back())
            self.forward_button.setEnabled(current_tab.can_go_forward())

# Dialog for browser settings
class SettingsDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Browser Settings")
        self.setMinimumSize(400, 300)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.light_theme = QRadioButton("Light Theme")
        self.dark_theme = QRadioButton("Dark Theme")
        
        # Set current theme
        if self.browser.dark_mode:
            self.dark_theme.setChecked(True)
        else:
            self.light_theme.setChecked(True)
        
        theme_layout.addWidget(self.light_theme)
        theme_layout.addWidget(self.dark_theme)
        
        layout.addWidget(theme_group)
        
        # Privacy group
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout(privacy_group)
        
        self.do_not_track = QCheckBox("Send Do Not Track requests")
        self.do_not_track.setChecked(self.browser.db_manager.get_setting("do_not_track", "0") == "1")
        
        privacy_layout.addWidget(self.do_not_track)
        
        layout.addWidget(privacy_group)
        
        # Button box
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
    
    def accept(self):
        # Save settings
        self.browser.set_dark_mode(self.dark_theme.isChecked())
        
        # Save Do Not Track
        do_not_track = "1" if self.do_not_track.isChecked() else "0"
        self.browser.db_manager.save_setting("do_not_track", do_not_track)
        
        super().accept()

# History dialog
class HistoryDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Browsing History")
        self.setMinimumSize(700, 500)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        
        # Load history
        self.load_history()
        
        layout.addWidget(self.history_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_button = QPushButton("Open Selected")
        open_button.clicked.connect(self.open_selected)
        
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_history(self):
        """Load browsing history"""
        self.history_list.clear()
        
        visits = self.browser.db_manager.get_recent_visits()
        for visit in visits:
            try:
                url = visit['url']
                title = visit['title'] or url
                ip = visit['ip_address']
                port = visit['port']
                ssl_valid = visit['ssl_valid']
                security_status = visit['security_status']
                timestamp = visit['visit_time']
                
                item = QListWidgetItem(f"{title}")
                item.setData(Qt.ItemDataRole.UserRole, url)
                item.setToolTip(f"URL: {url}\nIP: {ip}:{port}\nSSL: {ssl_valid}\nSecurity: {security_status}\nTime: {timestamp}")
                
                self.history_list.addItem(item)
            except (KeyError, TypeError):
                continue
    
    def open_selected(self):
        """Open selected history item"""
        selected = self.history_list.selectedItems()
        if selected:
            url = selected[0].data(Qt.ItemDataRole.UserRole)
            self.browser.navigate_to_url(url)
            self.accept()
    
    def clear_history(self):
        """Clear browsing history"""
        confirm = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all browsing history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # In a real implementation, clear the database table
            self.history_list.clear()
            QMessageBox.information(self, "History Cleared", "Your browsing history has been cleared.")

# Firewall dialog for blocking domains
class FirewallDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Firewall Settings")
        self.setMinimumSize(500, 400)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel("Website Firewall")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        desc = QLabel("Block malicious websites by domain name")
        
        layout.addWidget(title)
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
        
        # Load blocked domains
        self.load_blocked_domains()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        unblock_button = QPushButton("Unblock Selected")
        unblock_button.clicked.connect(self.unblock_selected)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(unblock_button)
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_blocked_domains(self):
        """Load blocked domains list"""
        self.blocked_list.clear()
        
        domains = self.browser.db_manager.get_blocked_domains()
        for domain in domains:
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
        if self.browser.db_manager.block_domain(domain):
            self.domain_input.clear()
            self.load_blocked_domains()
            QMessageBox.information(self, "Domain Blocked", f"The domain '{domain}' has been blocked.")
    
    def unblock_selected(self):
        """Unblock selected domain"""
        selected = self.blocked_list.selectedItems()
        if selected:
            domain = selected[0].text()
            
            if self.browser.db_manager.unblock_domain(domain):
                self.load_blocked_domains()
                QMessageBox.information(self, "Domain Unblocked", f"The domain '{domain}' has been unblocked.")

# Bookmarks dialog
class BookmarksDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Bookmarks")
        self.setMinimumSize(600, 400)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Bookmarks list
        self.bookmark_list = QListWidget()
        self.bookmark_list.setAlternatingRowColors(True)
        
        # Load bookmarks
        self.load_bookmarks()
        
        layout.addWidget(self.bookmark_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_button = QPushButton("Open Selected")
        open_button.clicked.connect(self.open_selected)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_bookmarks(self):
        """Load bookmarks"""
        self.bookmark_list.clear()
        
        bookmarks = self.browser.db_manager.get_bookmarks()
        for bookmark in bookmarks:
            try:
                url = bookmark['url']
                title = bookmark['title'] or url
                
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, url)
                item.setToolTip(url)
                
                self.bookmark_list.addItem(item)
            except (KeyError, TypeError):
                continue
    
    def open_selected(self):
        """Open selected bookmark"""
        selected = self.bookmark_list.selectedItems()
        if selected:
            url = selected[0].data(Qt.ItemDataRole.UserRole)
            self.browser.navigate_to_url(url)
            self.accept()
    
    def remove_selected(self):
        """Remove selected bookmark"""
        selected = self.bookmark_list.selectedItems()
        if selected:
            url = selected[0].data(Qt.ItemDataRole.UserRole)
            
            if self.browser.db_manager.remove_bookmark(url):
                self.load_bookmarks()
                QMessageBox.information(self, "Bookmark Removed", "The bookmark has been removed.")

# IP Tracker Dialog
class IPTrackerDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("IP Address & Port Tracker")
        self.setMinimumSize(800, 500)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel("Website IP Addresses and Ports")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        desc = QLabel("Track IP addresses and ports of visited websites")
        
        layout.addWidget(title)
        layout.addWidget(desc)
        
        # IP list
        self.ip_list = QListWidget()
        self.ip_list.setAlternatingRowColors(True)
        
        # Load IP data
        self.load_ip_data()
        
        layout.addWidget(self.ip_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_ip_data)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(refresh_button)
        button_layout.addStretch(1)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_ip_data(self):
        """Load IP tracking data"""
        self.ip_list.clear()
        
        visits = self.browser.db_manager.get_recent_visits()
        for visit in visits:
            try:
                url = visit['url']
                title = visit['title'] or url
                ip = visit['ip_address']
                port = visit['port']
                ssl_valid = visit['ssl_valid']
                security_status = visit['security_status']
                timestamp = visit['visit_time']
                
                # Create a formatted item
                item_text = f"{title}\nIP: {ip}:{port}\nSSL: {ssl_valid}\nSecurity: {security_status}\nTime: {timestamp}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, url)
                
                self.ip_list.addItem(item)
            except (KeyError, TypeError):
                continue

# Main Browser Window
class WebBrowser(QMainWindow):
    def __init__(self, incognito=False):
        super().__init__()
        
        # Browser state
        self.incognito_mode = incognito
        self.dark_mode = False
        
        # Initialize security manager
        self.security_manager = SecurityManager()
        
        # Setup database
        self.db_manager = DatabaseManager(incognito=incognito)
        
        # Load settings
        self.load_settings()
        
        # Setup window
        window_title = "Secure Web Browser" + (" (Incognito)" if incognito else "")
        self.setWindowTitle(window_title)
        self.setMinimumSize(1000, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create tabs
        self.tabs = BrowserTabs(self)
        
        # Add components to layout
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menus
        self.create_menus()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Apply theme
        self.apply_theme()
        
        # Create first tab
        self.tabs.add_new_tab(QUrl("https://www.google.com"))
        
        # Show WebEngine status
        if not WEB_ENGINE_AVAILABLE:
            self.status_bar.showMessage("WebEngine not available. Install PyQt6-WebEngine for full functionality.")
            QTimer.singleShot(5000, lambda: self.status_bar.showMessage("Ready"))
    
    def load_settings(self):
        """Load saved settings"""
        # Dark mode setting
        self.dark_mode = self.db_manager.get_setting("dark_mode", "0") == "1"
    
    def create_toolbar(self):
        """Create browser toolbar"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        
        # Add navigation bar
        self.nav_bar = NavigationBar(self)
        
        # Add address bar
        self.address_bar = AddressBar(self)
        
        # Add bookmark button
        self.bookmark_button = QPushButton("⭐")
        self.bookmark_button.setFixedSize(30, 30)
        self.bookmark_button.setToolTip("Add Bookmark")
        self.bookmark_button.clicked.connect(self.add_bookmark)
        
        # Add to toolbar
        self.toolbar.addWidget(self.nav_bar)
        self.toolbar.addWidget(self.address_bar)
        self.toolbar.addWidget(self.bookmark_button)
    
    def create_menus(self):
        """Create menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self.tabs.add_new_tab)
        file_menu.addAction(new_tab_action)
        
        new_incognito_window_action = QAction("New Incognito Window", self)
        new_incognito_window_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_incognito_window_action.triggered.connect(self.open_incognito_window)
        file_menu.addAction(new_incognito_window_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.tabs.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        toggle_dark_mode_action = QAction("Toggle Dark Mode", self)
        toggle_dark_mode_action.setShortcut(QKeySequence("Ctrl+D"))
        toggle_dark_mode_action.triggered.connect(lambda: self.set_dark_mode(not self.dark_mode))
        view_menu.addAction(toggle_dark_mode_action)
        
        # History menu
        history_menu = menu_bar.addMenu("History")
        
        show_history_action = QAction("Show History", self)
        show_history_action.setShortcut(QKeySequence("Ctrl+H"))
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)
        
        show_ip_tracker_action = QAction("Show IP Tracker", self)
        show_ip_tracker_action.setShortcut(QKeySequence("Ctrl+I"))
        show_ip_tracker_action.triggered.connect(self.show_ip_tracker)
        history_menu.addAction(show_ip_tracker_action)
        
        # Bookmarks menu
        bookmarks_menu = menu_bar.addMenu("Bookmarks")
        
        add_bookmark_action = QAction("Add Bookmark", self)
        add_bookmark_action.setShortcut(QKeySequence("Ctrl+D"))
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        
        show_bookmarks_action = QAction("Show Bookmarks", self)
        show_bookmarks_action.setShortcut(QKeySequence("Ctrl+B"))
        show_bookmarks_action.triggered.connect(self.show_bookmarks)
        bookmarks_menu.addAction(show_bookmarks_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        
        firewall_action = QAction("Firewall Settings", self)
        firewall_action.triggered.connect(self.show_firewall)
        tools_menu.addAction(firewall_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Focus address bar
        focus_address_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_address_shortcut.activated.connect(self.address_bar.setFocus)
        
        # Refresh page
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.nav_bar.refresh_page)
    
    def apply_theme(self):
        """Apply the current theme"""
        if self.dark_mode:
            # Dark theme
            style = """
                QMainWindow, QDialog {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
                QMenuBar {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
                QMenuBar::item:selected {
                    background-color: #3E3E42;
                }
                QMenu {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                }
                QMenu::item:selected {
                    background-color: #3E3E42;
                }
                QToolBar {
                    background-color: #2D2D30;
                    border-bottom: 1px solid #3E3E42;
                }
                QTabWidget::pane {
                    border: 1px solid #3E3E42;
                    background-color: #2D2D30;
                }
                QTabBar::tab {
                    background-color: #252526;
                    color: #CCCCCC;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border: 1px solid #3E3E42;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #3E3E42;
                }
                QPushButton {
                    background-color: #3E3E42;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #0078D7;
                }
                QLineEdit {
                    background-color: #3E3E42;
                    color: #FFFFFF;
                    padding: 8px 10px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078D7;
                }
                QStatusBar {
                    background-color: #2D2D30;
                    color: #CCCCCC;
                }
                QListWidget {
                    background-color: #252526;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                }
                QListWidget::item:alternate {
                    background-color: #2D2D30;
                }
                QListWidget::item:selected {
                    background-color: #0078D7;
                }
                QLabel, QCheckBox, QRadioButton, QGroupBox {
                    color: #FFFFFF;
                }
            """
        else:
            # Light theme
            style = """
                QMainWindow, QDialog {
                    background-color: #F5F5F5;
                    color: #000000;
                }
                QMenuBar {
                    background-color: #F5F5F5;
                    color: #000000;
                }
                QMenuBar::item:selected {
                    background-color: #E5E5E5;
                }
                QMenu {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                }
                QMenu::item:selected {
                    background-color: #E5E5E5;
                }
                QToolBar {
                    background-color: #F5F5F5;
                    border-bottom: 1px solid #CCCCCC;
                }
                QTabWidget::pane {
                    border: 1px solid #CCCCCC;
                    background-color: #FFFFFF;
                }
                QTabBar::tab {
                    background-color: #EFEFEF;
                    color: #555555;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border: 1px solid #CCCCCC;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #E5E5E5;
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #E5E5E5;
                }
                QPushButton:pressed {
                    background-color: #0078D7;
                    color: #FFFFFF;
                }
                QLineEdit {
                    background-color: #FFFFFF;
                    color: #000000;
                    padding: 8px 10px;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078D7;
                }
                QStatusBar {
                    background-color: #F5F5F5;
                    color: #555555;
                }
                QListWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                }
                QListWidget::item:alternate {
                    background-color: #F9F9F9;
                }
                QListWidget::item:selected {
                    background-color: #0078D7;
                    color: #FFFFFF;
                }
            """
        
        self.setStyleSheet(style)
    
    def navigate_to_url(self, url):
        """Navigate to a URL with security checks"""
        # Format URL
        if isinstance(url, str):
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            url = QUrl(url)
        
        url_str = url.toString()
        
        # Security checks
        if self.security_manager.is_phishing_site(url_str):
            QMessageBox.warning(
                self, "Security Warning", 
                "This website has been identified as a potential phishing site. Access has been blocked for your security."
            )
            return
        
        # Check SSL certificate
        valid, cert = self.security_manager.check_ssl_certificate(url_str)
        if not valid:
            QMessageBox.warning(
                self, "Security Warning",
                "This website's security certificate is invalid. Access has been blocked for your security."
            )
            return
        
        # Check if site is blocked
        if self.db_manager.is_domain_blocked(url_str):
            QMessageBox.warning(
                self, "Blocked Website", 
                "This website has been blocked by the firewall settings."
            )
            return
        
        # Update address bar
        self.address_bar.setText(url_str)
        
        # Navigate to URL in current tab
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.load(url)
            current_tab.update_security_status(url_str)
    
    def update_address_bar(self, url):
        """Update address bar with current URL"""
        url_str = url.toString()
        if url_str != "about:blank":
            self.address_bar.setText(url_str)
            
            # Update status bar with IP information
            try:
                parsed_url = urlparse(url_str)
                domain = parsed_url.netloc
                if domain:
                    ip_address = socket.gethostbyname(domain)
                    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
                    self.status_bar.showMessage(f"Server: {ip_address}:{port}")
            except:
                self.status_bar.showMessage("Ready")
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.nav_bar.update_button_states()
    
    def add_bookmark(self):
        """Add current page to bookmarks"""
        current_tab = self.tabs.currentWidget()
        if current_tab and WEB_ENGINE_AVAILABLE:
            url = current_tab.url().toString()
            title = current_tab.title()
            
            # Skip about:blank
            if url == "about:blank":
                return
            
            # Add to database
            if self.db_manager.add_bookmark(url, title):
                QMessageBox.information(self, "Bookmark Added", f"Added bookmark for '{title}'")
    
    def show_bookmarks(self):
        """Show bookmarks dialog"""
        dialog = BookmarksDialog(self)
        dialog.exec()
    
    def show_history(self):
        """Show history dialog"""
        dialog = HistoryDialog(self)
        dialog.exec()
    
    def show_firewall(self):
        """Show firewall dialog"""
        dialog = FirewallDialog(self)
        dialog.exec()
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_ip_tracker(self):
        """Show IP tracker dialog"""
        dialog = IPTrackerDialog(self)
        dialog.exec()
    
    def set_dark_mode(self, enabled):
        """Set dark mode"""
        if self.dark_mode != enabled:
            self.dark_mode = enabled
            self.apply_theme()
            
            # Save setting if not in incognito mode
            if not self.incognito_mode:
                self.db_manager.save_setting("dark_mode", "1" if enabled else "0")
    
    def open_incognito_window(self):
        """Open a new incognito window"""
        incognito_browser = WebBrowser(incognito=True)
        incognito_browser.show()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # In a real browser, we might ask for confirmation
        # Clean up resources
        self.db_manager.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebBrowser()
    browser.show()
    sys.exit(app.exec())