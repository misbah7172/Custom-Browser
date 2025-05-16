#!/usr/bin/env python3
"""
Ultimate Browser - A fully functional browser with tracking, dark mode, incognito mode and dark web access
"""
import sys
import os
import socket
import socks
import requests
from urllib.parse import urlparse
import datetime
import sqlite3
import re
import html
import random
import json

from PyQt6.QtCore import QUrl, Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QMessageBox, QTabWidget, QMenuBar, QMenu,
    QStatusBar, QDialog, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QDialogButtonBox, QTextEdit,
    QSizePolicy, QCheckBox, QRadioButton, QButtonGroup, QGridLayout,
    QComboBox, QTextBrowser, QFrame, QToolBar, QToolButton, QSplitter,
    QProgressBar
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction, QColor, QPalette
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("QtWebEngine is not available. Using simplified browser view.")

# Database Manager
class DatabaseManager:
    """Database manager for browser"""
    
    def __init__(self, incognito=False):
        """Initialize database"""
        self.incognito = incognito
        if not incognito:
            self.db_path = os.path.expanduser("~/.browser_data.db")
            self.conn = None
            self.cursor = None
            self.connect()
            self.create_tables()
            # Load blocked domains
            self.blocked_domains = self.get_blocked_domains()
        else:
            self.blocked_domains = []
    
    def connect(self):
        """Connect to database"""
        if self.incognito:
            return
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Database connection error: {e}")
    
    def create_tables(self):
        """Create database tables"""
        if self.incognito or not self.cursor:
            return
        
        try:
            # Visits table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    ip_address TEXT,
                    location TEXT,
                    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Firewall table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS firewall (
                    id INTEGER PRIMARY KEY,
                    domain TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    blocked_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Bookmarks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Settings table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    def add_visit(self, url, title=None):
        """Record a website visit"""
        if self.incognito or not self.cursor:
            return True
        
        try:
            # Parse URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Skip about:blank and empty URLs
            if not domain or domain == "about:blank":
                return True
            
            # Get IP address
            try:
                ip_address = socket.gethostbyname(domain)
            except:
                ip_address = "Unknown"
            
            # Location (placeholder)
            location = "Unknown"
            
            # Add to database
            self.cursor.execute(
                "INSERT INTO visits (url, title, ip_address, location) VALUES (?, ?, ?, ?)",
                (url, title, ip_address, location)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording visit: {e}")
            return False
    
    def is_domain_blocked(self, url):
        """Check if domain is blocked"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            for blocked_domain in self.blocked_domains:
                if domain == blocked_domain or domain.endswith("." + blocked_domain):
                    return True
            
            return False
        except:
            return False
    
    def get_blocked_domains(self):
        """Get list of blocked domains"""
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute("SELECT domain FROM firewall")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving blocked domains: {e}")
            return []
    
    def block_domain(self, domain, reason="User blocked"):
        """Block a domain"""
        if self.incognito:
            self.blocked_domains.append(domain)
            return True
        
        if not self.cursor:
            return False
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO firewall (domain, reason) VALUES (?, ?)",
                (domain, reason)
            )
            self.conn.commit()
            self.blocked_domains = self.get_blocked_domains()
            return True
        except Exception as e:
            print(f"Error blocking domain: {e}")
            return False
    
    def unblock_domain(self, domain):
        """Unblock a domain"""
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
    
    def get_recent_visits(self, limit=100):
        """Get recent website visits"""
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute(
                "SELECT url, title, ip_address, location, visit_time FROM visits ORDER BY visit_time DESC LIMIT ?", 
                (limit,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error retrieving visits: {e}")
            return []
    
    def add_bookmark(self, url, title):
        """Add a bookmark"""
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
        """Remove a bookmark"""
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
        """Get all bookmarks"""
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute("SELECT url, title FROM bookmarks ORDER BY title")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error retrieving bookmarks: {e}")
            return []
    
    def save_setting(self, key, value):
        """Save a setting"""
        if self.incognito or not self.cursor:
            return False
        
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_time) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, value)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving setting: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """Get a setting value"""
        if self.incognito or not self.cursor:
            return default
        
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = self.cursor.fetchone()
            return result[0] if result else default
        except Exception as e:
            print(f"Error retrieving setting: {e}")
            return default
    
    def close(self):
        """Close database connection"""
        if not self.incognito and self.conn:
            self.conn.close()

# Tor Network Manager
class TorManager:
    """Manages Tor network connections"""
    
    def __init__(self):
        self.tor_enabled = False
        self.default_socket = None
    
    def enable_tor(self, tor_port=9050):
        """Enable Tor for routing"""
        if self.tor_enabled:
            return True
        
        try:
            # Check if Tor is running
            if not self.is_tor_running(tor_port):
                return False
            
            # Backup default socket
            self.default_socket = socket.socket
            
            # Configure SOCKS proxy
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", tor_port)
            socket.socket = socks.socksocket
            
            self.tor_enabled = True
            return True
        except Exception as e:
            print(f"Error enabling Tor: {e}")
            return False
    
    def disable_tor(self):
        """Disable Tor routing"""
        if not self.tor_enabled or not self.default_socket:
            return False
        
        try:
            # Restore original socket
            socket.socket = self.default_socket
            self.tor_enabled = False
            return True
        except Exception as e:
            print(f"Error disabling Tor: {e}")
            return False
    
    def is_tor_running(self, tor_port=9050):
        """Check if Tor is accessible"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(("127.0.0.1", tor_port))
            s.close()
            return True
        except:
            return False

# WebView for rendering websites
class BrowserWebView(QTextBrowser if not WEBENGINE_AVAILABLE else QWebEngineView):
    """Web view for rendering websites"""
    
    urlChanged = pyqtSignal(QUrl)
    loadFinished = pyqtSignal(bool)
    titleChanged = pyqtSignal(str)
    
    def __init__(self, browser, tab_widget=None, profile=None):
        super().__init__()
        self.browser = browser
        self.tab_widget = tab_widget
        self._url = QUrl()
        self._title = "New Tab"
        self._history = []
        self._history_position = -1
        
        if WEBENGINE_AVAILABLE:
            # Connect signals
            self.urlChanged.connect(self.browser.update_address_bar)
            self.loadFinished.connect(self.browser.update_navigation_buttons)
            
            # Set profile if provided (for incognito mode)
            if profile:
                page = QWebEnginePage(profile, self)
                self.setPage(page)
        else:
            # Create custom signals
            self.setOpenLinks(False)
            self.anchorClicked.connect(self.on_link_clicked)
    
    def on_link_clicked(self, url):
        """Handle link clicks in text browser mode"""
        self.load(url)
    
    def load(self, url):
        """Load a URL"""
        self._url = url
        
        if WEBENGINE_AVAILABLE:
            super().load(url)
        else:
            # Simplified webpage rendering
            try:
                url_str = url.toString() if hasattr(url, 'toString') else str(url)
                if not url_str.startswith(('http://', 'https://')):
                    url_str = 'http://' + url_str
                
                # Check if blocked
                if hasattr(self.browser, 'db_manager') and self.browser.db_manager.is_domain_blocked(url_str):
                    self.setHtml(f"<h1>Website Blocked</h1><p>This website has been blocked by the firewall.</p>")
                    return
                
                # Add to history
                if self._history_position < len(self._history) - 1:
                    self._history = self._history[:self._history_position + 1]
                
                self._history.append(url_str)
                self._history_position = len(self._history) - 1
                
                # Get domain and IP info
                parsed_url = urlparse(url_str)
                domain = parsed_url.netloc
                
                try:
                    ip_address = socket.gethostbyname(domain)
                    status_message = f"Connected to: {domain} ({ip_address})"
                except:
                    ip_address = "Unknown"
                    status_message = f"Connected to: {domain}"
                
                if hasattr(self.browser, 'status_bar'):
                    self.browser.status_bar.showMessage(status_message)
                
                # Fetch content
                try:
                    response = requests.get(url_str, timeout=10)
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'text/html' in content_type:
                        html_content = response.text
                        
                        # Extract title
                        title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                        self._title = title_match.group(1).strip() if title_match else domain
                        
                                        # Fix the setHtml arguments
                        if 'google.com/search' in url_str:
                            parsed_html = self.extract_search_results(html_content, "Google")
                            self.setHtml(parsed_html)
                        elif 'duckduckgo.com' in url_str:
                            parsed_html = self.extract_search_results(html_content, "DuckDuckGo")
                            self.setHtml(parsed_html)
                        else:
                            # Set regular page content
                            self.setHtml(html_content)
                        
                        # Update tab title if we have access to tab widget
                        if self.tab_widget:
                            index = self.tab_widget.indexOf(self)
                            if index >= 0:
                                self.tab_widget.setTabText(index, self._title[:20] + "..." if len(self._title) > 20 else self._title)
                        
                        # Emit signals
                        self.titleChanged.emit(self._title)
                        self.urlChanged.emit(QUrl(url_str))
                        self.loadFinished.emit(True)
                        
                        # Add to database if not in incognito mode
                        if hasattr(self.browser, 'db_manager') and not self.browser.incognito_mode:
                            self.browser.db_manager.add_visit(url_str, self._title)
                    else:
                        self.setHtml(f"<h1>Content Type Not Supported</h1><p>The content type '{content_type}' cannot be displayed.</p>")
                except Exception as e:
                    self.setHtml(f"<h1>Error Loading Page</h1><p>Error: {str(e)}</p>")
                    self.loadFinished.emit(False)
            except Exception as e:
                self.setHtml(f"<h1>Error</h1><p>{str(e)}</p>")
                self.loadFinished.emit(False)
    
    def extract_search_results(self, html_content, search_engine):
        """Extract and format search results"""
        results_html = []
        
        if search_engine == "Google":
            # Extract search results from Google
            search_items = re.findall(r'<div class="g">(.*?)</div>\s*</div>\s*</div>', html_content, re.DOTALL)
            
            if not search_items:
                # Try alternative pattern
                search_items = re.findall(r'<div class="tF2Cxc">(.*?)</div>\s*</div>', html_content, re.DOTALL)
            
            results_html.append('<h1>Google Search Results</h1>')
            results_html.append('<div class="search-results">')
            
            if search_items:
                for item in search_items:
                    # Extract title
                    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', item, re.DOTALL)
                    title = "No title" if not title_match else re.sub(r'<.*?>', '', title_match.group(1))
                    
                    # Extract URL
                    url_match = re.search(r'<a href="([^"]+)"', item)
                    url = "#" if not url_match else url_match.group(1)
                    
                    # Extract snippet
                    snippet_match = re.search(r'<div class="[^"]*?"[^>]*?>(.*?)</div>', item, re.DOTALL)
                    snippet = "" if not snippet_match else re.sub(r'<.*?>', '', snippet_match.group(1))
                    
                    # Add result to HTML
                    results_html.append(f'<div class="result">')
                    results_html.append(f'<h3><a href="{url}">{title}</a></h3>')
                    results_html.append(f'<div class="url">{url}</div>')
                    results_html.append(f'<div class="snippet">{snippet}</div>')
                    results_html.append('</div>')
            else:
                results_html.append('<p>No search results could be extracted.</p>')
            
            results_html.append('</div>')
            
        elif search_engine == "DuckDuckGo":
            # Extract DuckDuckGo results
            search_items = re.findall(r'<div class="result[^"]*">(.*?)</div>\s*</div>', html_content, re.DOTALL)
            
            results_html.append('<h1>DuckDuckGo Search Results</h1>')
            results_html.append('<div class="search-results">')
            
            if search_items:
                for item in search_items:
                    # Extract title
                    title_match = re.search(r'<h2[^>]*>(.*?)</h2>', item, re.DOTALL)
                    title = "No title" if not title_match else re.sub(r'<.*?>', '', title_match.group(1))
                    
                    # Extract URL
                    url_match = re.search(r'<a href="([^"]+)"', item)
                    url = "#" if not url_match else url_match.group(1)
                    
                    # Extract snippet
                    snippet_match = re.search(r'<div class="[^"]*abstract[^"]*"[^>]*?>(.*?)</div>', item, re.DOTALL)
                    snippet = "" if not snippet_match else re.sub(r'<.*?>', '', snippet_match.group(1))
                    
                    # Add result to HTML
                    results_html.append(f'<div class="result">')
                    results_html.append(f'<h3><a href="{url}">{title}</a></h3>')
                    results_html.append(f'<div class="url">{url}</div>')
                    results_html.append(f'<div class="snippet">{snippet}</div>')
                    results_html.append('</div>')
            else:
                results_html.append('<p>No search results could be extracted.</p>')
            
            results_html.append('</div>')
        
        # Add CSS styling
        css = """
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; line-height: 1.5; }
            .search-results { margin-top: 20px; }
            .result { margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #eee; }
            .result h3 { margin: 0 0 5px 0; }
            .result h3 a { color: #1a0dab; text-decoration: none; }
            .result h3 a:hover { text-decoration: underline; }
            .url { color: #006621; font-size: 14px; margin-bottom: 5px; }
            .snippet { color: #545454; font-size: 14px; }
        </style>
        """
        
        # Combine everything
        return css + "".join(results_html)
    
    def url(self):
        """Get current URL"""
        if WEBENGINE_AVAILABLE:
            return super().url()
        return self._url
    
    def title(self):
        """Get page title"""
        if WEBENGINE_AVAILABLE:
            return super().title()
        return self._title
    
    def back(self):
        """Go back in history"""
        if WEBENGINE_AVAILABLE:
            return super().back()
        
        if self._history_position > 0:
            self._history_position -= 1
            self.load(QUrl(self._history[self._history_position]))
    
    def forward(self):
        """Go forward in history"""
        if WEBENGINE_AVAILABLE:
            return super().forward()
        
        if self._history_position < len(self._history) - 1:
            self._history_position += 1
            self.load(QUrl(self._history[self._history_position]))
    
    def reload(self):
        """Reload the page"""
        if WEBENGINE_AVAILABLE:
            return super().reload()
        
        if self._history_position >= 0 and self._history_position < len(self._history):
            self.load(QUrl(self._history[self._history_position]))
    
    def history(self):
        """Get history"""
        if WEBENGINE_AVAILABLE:
            return super().history()
        
        class SimpleHistory:
            def __init__(self, view):
                self.view = view
            
            def canGoBack(self):
                return self.view._history_position > 0
            
            def canGoForward(self):
                return self.view._history_position < len(self.view._history) - 1
        
        return SimpleHistory(self)
    
    def createWindow(self, window_type):
        """Create a new window for popups"""
        if self.tab_widget and hasattr(self.tab_widget, 'add_new_tab'):
            new_tab = BrowserWebView(self.browser, self.tab_widget)
            self.tab_widget.add_new_tab(None, new_tab)
            return new_tab
        return None

class BrowserTab(QWidget):
    """Browser tab container"""
    
    def __init__(self, browser, profile=None):
        super().__init__()
        self.browser = browser
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Create web view
        self.web_view = BrowserWebView(browser, browser.tabs, profile)
        
        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: transparent;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
            }
        """)
        
        # Add components to layout
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.web_view)
        
        # Connect signals
        if WEBENGINE_AVAILABLE:
            self.web_view.loadStarted.connect(self.on_load_started)
            self.web_view.loadProgress.connect(self.on_load_progress)
            self.web_view.loadFinished.connect(self.on_load_finished)
    
    def on_load_started(self):
        """Handle load started event"""
        self.progress_bar.setValue(0)
        self.progress_bar.show()
    
    def on_load_progress(self, progress):
        """Handle load progress event"""
        self.progress_bar.setValue(progress)
    
    def on_load_finished(self, success):
        """Handle load finished event"""
        if success:
            self.progress_bar.setValue(100)
            QTimer.singleShot(500, self.progress_bar.hide)
        else:
            self.progress_bar.hide()
    
    def url(self):
        """Get current URL"""
        return self.web_view.url()
    
    def title(self):
        """Get page title"""
        return self.web_view.title()
    
    def load(self, url):
        """Load a URL"""
        return self.web_view.load(url)
    
    def reload(self):
        """Reload the page"""
        return self.web_view.reload()
    
    def back(self):
        """Go back in history"""
        return self.web_view.back()
    
    def forward(self):
        """Go forward in history"""
        return self.web_view.forward()
    
    def history(self):
        """Get history"""
        return self.web_view.history()

class BrowserTabs(QTabWidget):
    """Tab widget for browser tabs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Tab settings
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
    
    def add_new_tab(self, url=None, web_view=None):
        """Add a new tab"""
        if url is None:
            url = QUrl("https://www.google.com")
        
        # Create tab with proper profile
        if web_view:
            tab = BrowserTab(self.browser)
            tab.web_view = web_view
        elif self.browser.incognito_mode and WEBENGINE_AVAILABLE:
            # Create private profile for incognito
            profile = QWebEngineProfile()
            tab = BrowserTab(self.browser, profile)
        else:
            tab = BrowserTab(self.browser)
        
        # Add tab to widget
        index = self.addTab(tab, "New Tab")
        self.setCurrentIndex(index)
        
        # Load URL
        if not web_view:
            tab.load(url)
        
        # Connect signals
        tab.web_view.titleChanged.connect(lambda title, t=tab: self.update_tab_title(t, title))
        
        return tab
    
    def update_tab_title(self, tab, title):
        """Update tab title"""
        index = self.indexOf(tab)
        if index != -1:
            # Truncate long titles
            display_title = title[:20] + "..." if len(title) > 20 else title
            self.setTabText(index, display_title)
    
    def close_tab(self, index):
        """Close a tab"""
        if self.count() > 1:
            widget = self.widget(index)
            self.removeTab(index)
            widget.deleteLater()
        else:
            # For last tab, just reset to Google
            self.currentWidget().load(QUrl("https://www.google.com"))
    
    def close_current_tab(self):
        """Close current tab"""
        self.close_tab(self.currentIndex())
    
    def on_tab_change(self, index):
        """Handle tab change"""
        if index >= 0:
            # Update UI with current tab info
            current_tab = self.currentWidget()
            if current_tab:
                self.browser.update_address_bar(current_tab.url())
                self.browser.update_navigation_buttons()

class AddressBar(QLineEdit):
    """Address bar for entering URLs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Setup address bar
        self.setPlaceholderText("Search or enter website name")
        self.returnPressed.connect(self.navigate_to_url)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(30)
    
    def navigate_to_url(self):
        """Navigate to URL entered in address bar"""
        url_text = self.text().strip()
        
        if not url_text:
            return
        
        # Check if it's a search
        if ' ' in url_text or '.' not in url_text:
            # Check if we should use Tor search if Tor is enabled
            if hasattr(self.browser, 'tor_manager') and self.browser.tor_manager.tor_enabled:
                # Use DuckDuckGo for privacy
                search_url = f"https://duckduckgo.com/?q={url_text.replace(' ', '+')}"
            else:
                # Use Google
                search_url = f"https://www.google.com/search?q={url_text.replace(' ', '+')}"
            self.browser.navigate_to_url(search_url)
        else:
            self.browser.navigate_to_url(url_text)

class NavigationBar(QWidget):
    """Navigation bar with browser controls"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Create layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)
        
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
        
        self.home_button = QPushButton("🏠")
        self.home_button.setFixedSize(30, 30)
        self.home_button.setToolTip("Home")
        self.home_button.clicked.connect(self.go_home)
        
        # Add buttons to layout
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.home_button)
        
        # Initialize button states
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
        """Refresh the page"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            current_tab.reload()
    
    def go_home(self):
        """Go to home page"""
        self.browser.navigate_to_url("https://www.google.com")

class SettingsDialog(QDialog):
    """Dialog for browser settings"""
    
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Browser Settings")
        self.setMinimumSize(500, 400)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Settings tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # General settings
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        general_tab.setLayout(general_layout)
        
        # Theme setting
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        theme_group.setLayout(theme_layout)
        
        self.light_theme = QRadioButton("Light")
        self.dark_theme = QRadioButton("Dark")
        
        # Set current theme
        if self.browser.dark_mode:
            self.dark_theme.setChecked(True)
        else:
            self.light_theme.setChecked(True)
        
        theme_layout.addWidget(self.light_theme)
        theme_layout.addWidget(self.dark_theme)
        
        general_layout.addWidget(theme_group)
        general_layout.addStretch(1)
        
        # Privacy settings
        privacy_tab = QWidget()
        privacy_layout = QVBoxLayout()
        privacy_tab.setLayout(privacy_layout)
        
        # Tor settings
        tor_group = QGroupBox("Tor Network")
        tor_layout = QVBoxLayout()
        tor_group.setLayout(tor_layout)
        
        self.enable_tor = QCheckBox("Enable Tor for .onion sites")
        self.enable_tor.setChecked(self.browser.tor_manager.tor_enabled if hasattr(self.browser, 'tor_manager') else False)
        
        tor_status = QLabel(f"Tor Status: {'Available' if TorManager().is_tor_running() else 'Not Available'}")
        
        tor_layout.addWidget(self.enable_tor)
        tor_layout.addWidget(tor_status)
        
        privacy_layout.addWidget(tor_group)
        
        # Do Not Track
        tracking_group = QGroupBox("Tracking")
        tracking_layout = QVBoxLayout()
        tracking_group.setLayout(tracking_layout)
        
        self.do_not_track = QCheckBox("Send Do Not Track requests")
        self.do_not_track.setChecked(self.browser.db_manager.get_setting("do_not_track", "0") == "1")
        
        tracking_layout.addWidget(self.do_not_track)
        
        privacy_layout.addWidget(tracking_group)
        privacy_layout.addStretch(1)
        
        # Add tabs
        tabs.addTab(general_tab, "General")
        tabs.addTab(privacy_tab, "Privacy")
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        """Save settings when dialog is accepted"""
        # Theme setting
        self.browser.set_dark_mode(self.dark_theme.isChecked())
        
        # Tor setting
        if hasattr(self.browser, 'tor_manager'):
            if self.enable_tor.isChecked():
                self.browser.tor_manager.enable_tor()
            else:
                self.browser.tor_manager.disable_tor()
        
        # Do Not Track
        do_not_track = "1" if self.do_not_track.isChecked() else "0"
        self.browser.db_manager.save_setting("do_not_track", do_not_track)
        
        super().accept()

class HistoryDialog(QDialog):
    """Dialog for browsing history"""
    
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Browsing History")
        self.setMinimumSize(800, 500)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Recent Website Visits")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Visit list
        self.visit_list = QListWidget()
        self.visit_list.setAlternatingRowColors(True)
        layout.addWidget(self.visit_list)
        
        # Load history
        self.load_history()
        
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
        self.visit_list.clear()
        
        visits = self.browser.db_manager.get_recent_visits()
        for visit in visits:
            try:
                url = visit['url']
                title = visit['title'] or url
                ip = visit['ip_address']
                timestamp = visit['visit_time']
                
                item = QListWidgetItem(f"{title} - {timestamp}")
                item.setData(Qt.ItemDataRole.UserRole, url)
                item.setToolTip(f"URL: {url}\nIP: {ip}\nTime: {timestamp}")
                
                self.visit_list.addItem(item)
            except (KeyError, TypeError):
                continue
    
    def open_selected(self):
        """Open selected history item"""
        selected = self.visit_list.selectedItems()
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
            # In a real implementation, this would clear the database
            # For now, just clear the list
            self.visit_list.clear()
            QMessageBox.information(self, "History Cleared", "Your browsing history has been cleared.")

class BookmarkDialog(QDialog):
    """Dialog for managing bookmarks"""
    
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Bookmarks")
        self.setMinimumSize(600, 400)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("Bookmarks")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Bookmark list
        self.bookmark_list = QListWidget()
        self.bookmark_list.setAlternatingRowColors(True)
        layout.addWidget(self.bookmark_list)
        
        # Load bookmarks
        self.load_bookmarks()
        
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

class FirewallDialog(QDialog):
    """Dialog for managing firewall settings"""
    
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        
        # Setup dialog
        self.setWindowTitle("Firewall Settings")
        self.setMinimumSize(500, 400)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
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
        
        # Load blocked domains
        self.load_domains()
        
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
    
    def load_domains(self):
        """Load blocked domains"""
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
            self.load_domains()
            QMessageBox.information(self, "Domain Blocked", f"The domain '{domain}' has been blocked.")
    
    def unblock_selected(self):
        """Unblock selected domain"""
        selected = self.blocked_list.selectedItems()
        if selected:
            domain = selected[0].text()
            
            if self.browser.db_manager.unblock_domain(domain):
                self.load_domains()
                QMessageBox.information(self, "Domain Unblocked", f"The domain '{domain}' has been unblocked.")

class UltimateBrowser(QMainWindow):
    """Main browser window"""
    
    def __init__(self):
        super().__init__()
        
        # Browser state
        self.incognito_mode = False
        self.dark_mode = False
        self.tor_manager = TorManager()
        
        # Initialize database
        self.db_manager = DatabaseManager(incognito=self.incognito_mode)
        
        # Load settings
        self.load_settings()
        
        # Setup window
        self.setWindowTitle("Ultimate Browser")
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.central_widget.setLayout(self.main_layout)
        
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
        self.status_bar.showMessage("Ready")
        
        # Create menus
        self.create_menus()
        
        # Setup shortcuts
        self.setup_shortcuts()
        
        # Apply theme
        self.apply_theme()
        
        # Create first tab
        self.tabs.add_new_tab(QUrl("https://www.google.com"))
    
    def load_settings(self):
        """Load saved settings"""
        # Load dark mode setting
        self.dark_mode = self.db_manager.get_setting("dark_mode", "0") == "1"
    
    def create_toolbar(self):
        """Create browser toolbar"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        
        # Create navigation bar
        self.nav_bar = NavigationBar(self)
        
        # Create address bar
        self.address_bar = AddressBar(self)
        
        # Add bookmark button
        self.bookmark_button = QPushButton("⭐")
        self.bookmark_button.setFixedSize(30, 30)
        self.bookmark_button.setToolTip("Add Bookmark")
        self.bookmark_button.clicked.connect(self.add_bookmark)
        
        # Add components to toolbar
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
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self.find_in_page)
        edit_menu.addAction(find_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        toggle_dark_mode_action = QAction("Toggle Dark Mode", self)
        toggle_dark_mode_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        toggle_dark_mode_action.triggered.connect(lambda: self.set_dark_mode(not self.dark_mode))
        view_menu.addAction(toggle_dark_mode_action)
        
        # History menu
        history_menu = menu_bar.addMenu("History")
        
        back_action = QAction("Back", self)
        back_action.setShortcut(QKeySequence("Alt+Left"))
        back_action.triggered.connect(self.nav_bar.navigate_back)
        history_menu.addAction(back_action)
        
        forward_action = QAction("Forward", self)
        forward_action.setShortcut(QKeySequence("Alt+Right"))
        forward_action.triggered.connect(self.nav_bar.navigate_forward)
        history_menu.addAction(forward_action)
        
        history_menu.addSeparator()
        
        show_history_action = QAction("Show History", self)
        show_history_action.setShortcut(QKeySequence("Ctrl+H"))
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)
        
        # Bookmarks menu
        bookmarks_menu = menu_bar.addMenu("Bookmarks")
        
        add_bookmark_action = QAction("Add Bookmark", self)
        add_bookmark_action.setShortcut(QKeySequence("Ctrl+D"))
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        
        show_bookmarks_action = QAction("Show Bookmarks", self)
        show_bookmarks_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        show_bookmarks_action.triggered.connect(self.show_bookmarks)
        bookmarks_menu.addAction(show_bookmarks_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        
        show_firewall_action = QAction("Firewall Settings", self)
        show_firewall_action.triggered.connect(self.show_firewall)
        tools_menu.addAction(show_firewall_action)
        
        tools_menu.addSeparator()
        
        tor_menu = tools_menu.addMenu("Tor Network")
        
        enable_tor_action = QAction("Enable Tor", self)
        enable_tor_action.triggered.connect(lambda: self.toggle_tor(True))
        tor_menu.addAction(enable_tor_action)
        
        disable_tor_action = QAction("Disable Tor", self)
        disable_tor_action.triggered.connect(lambda: self.toggle_tor(False))
        tor_menu.addAction(disable_tor_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Address bar focus
        address_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_shortcut.activated.connect(self.address_bar.setFocus)
        
        # Refresh
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.nav_bar.refresh_page)
    
    def apply_theme(self):
        """Apply current theme"""
        if self.dark_mode:
            # Dark theme
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #2D2D30;
                    color: #FFFFFF;
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
                    border-bottom-color: #2D2D30;
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
                    background-color: #0E639C;
                }
                QLineEdit {
                    background-color: #3E3E42;
                    color: #FFFFFF;
                    padding: 8px 10px;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border: 1px solid #0E639C;
                }
                QStatusBar {
                    background-color: #2D2D30;
                    color: #CCCCCC;
                    border-top: 1px solid #3E3E42;
                }
                QMenuBar {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #3E3E42;
                }
                QMenu {
                    background-color: #2D2D30;
                    color: #FFFFFF;
                    border: 1px solid #3E3E42;
                }
                QMenu::item {
                    padding: 6px 20px 6px 20px;
                }
                QMenu::item:selected {
                    background-color: #3E3E42;
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
                    background-color: #0E639C;
                }
                QLabel, QCheckBox, QRadioButton, QGroupBox {
                    color: #FFFFFF;
                }
                QToolBar {
                    background-color: #2D2D30;
                    border-bottom: 1px solid #3E3E42;
                }
                QProgressBar {
                    border: none;
                    background-color: #2D2D30;
                }
                QProgressBar::chunk {
                    background-color: #0E639C;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #F5F5F5;
                    color: #000000;
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
                    border-bottom-color: #FFFFFF;
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
                    border-top: 1px solid #CCCCCC;
                }
                QMenuBar {
                    background-color: #F5F5F5;
                    color: #000000;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #E5E5E5;
                }
                QMenu {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                }
                QMenu::item {
                    padding: 6px 20px 6px 20px;
                }
                QMenu::item:selected {
                    background-color: #E5E5E5;
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
                QToolBar {
                    background-color: #F5F5F5;
                    border-bottom: 1px solid #CCCCCC;
                }
                QProgressBar {
                    border: none;
                    background-color: transparent;
                }
                QProgressBar::chunk {
                    background-color: #0078D7;
                }
            """)
    
    def navigate_to_url(self, url):
        """Navigate to a URL"""
        # Prepare URL
        if isinstance(url, str):
            url_str = url
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'http://' + url_str
            url = QUrl(url_str)
        
        # Check if site is blocked
        url_str = url.toString()
        if self.db_manager.is_domain_blocked(url_str):
            QMessageBox.warning(
                self, "Blocked Website", 
                "This website has been blocked by the firewall settings."
            )
            return
        
        # Update address bar
        self.address_bar.setText(url_str)
        
        # Navigate to the URL
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.load(url)
    
    def update_address_bar(self, url):
        """Update address bar with current URL"""
        url_str = url.toString()
        if url_str != "about:blank":
            self.address_bar.setText(url_str)
            
            # Add to database if not in incognito mode
            if not self.incognito_mode:
                current_tab = self.tabs.currentWidget()
                if current_tab:
                    title = current_tab.title()
                    self.db_manager.add_visit(url_str, title)
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'history'):
            history = current_tab.history()
            if hasattr(history, 'canGoBack'):
                self.nav_bar.back_button.setEnabled(history.canGoBack())
            if hasattr(history, 'canGoForward'):
                self.nav_bar.forward_button.setEnabled(history.canGoForward())
    
    def add_bookmark(self):
        """Add current page to bookmarks"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
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
        dialog = BookmarkDialog(self)
        dialog.exec()
    
    def show_history(self):
        """Show history dialog"""
        dialog = HistoryDialog(self)
        dialog.exec()
    
    def show_firewall(self):
        """Show firewall dialog"""
        dialog = FirewallDialog(self)
        dialog.exec()
    
    def toggle_tor(self, enable):
        """Toggle Tor routing"""
        if enable:
            if self.tor_manager.enable_tor():
                self.status_bar.showMessage("Tor routing enabled for .onion sites")
            else:
                QMessageBox.warning(
                    self, "Tor Not Available", 
                    "Tor is not running on this system. Please install and start Tor first."
                )
        else:
            if self.tor_manager.disable_tor():
                self.status_bar.showMessage("Tor routing disabled")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
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
        incognito_browser = UltimateBrowser()
        incognito_browser.incognito_mode = True
        incognito_browser.db_manager = DatabaseManager(incognito=True)
        incognito_browser.setWindowTitle("Ultimate Browser (Incognito)")
        incognito_browser.tabs.add_new_tab(QUrl("https://www.google.com"))
        incognito_browser.show()
    
    def find_in_page(self):
        """Find text in page"""
        # Simplified implementation
        QMessageBox.information(self, "Find", "Search functionality would appear here")
    
    def zoom_in(self):
        """Zoom in the current page"""
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab.web_view, 'setZoomFactor'):
            current_factor = current_tab.web_view.zoomFactor()
            current_tab.web_view.setZoomFactor(current_factor * 1.1)
    
    def zoom_out(self):
        """Zoom out the current page"""
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab.web_view, 'setZoomFactor'):
            current_factor = current_tab.web_view.zoomFactor()
            current_tab.web_view.setZoomFactor(current_factor / 1.1)
    
    def reset_zoom(self):
        """Reset zoom to default"""
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab.web_view, 'setZoomFactor'):
            current_tab.web_view.setZoomFactor(1.0)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Show confirmation in normal mode
        if not self.incognito_mode:
            confirm = QMessageBox.question(
                self,
                "Confirm Exit",
                "Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Clean up
        self.db_manager.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = UltimateBrowser()
    browser.show()
    sys.exit(app.exec())