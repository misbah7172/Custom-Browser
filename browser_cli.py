#!/usr/bin/env python3
"""
Console-based web browser with tracking and firewall features
"""
import os
import sys
import re
import json
import sqlite3
import socket
import webbrowser
from urllib.parse import urlparse, quote_plus
import datetime
from html.parser import HTMLParser
# Import libraries for web requests
import urllib.request
import urllib.parse
import urllib.error

# Check if requests is properly available 
try:
    import requests
    # Test if requests works properly
    requests.get
    REQUESTS_AVAILABLE = True
except (ImportError, AttributeError):
    REQUESTS_AVAILABLE = False
    print("Using built-in urllib for web requests.")

# Database Manager for tracking
class DatabaseManager:
    def __init__(self, incognito=False):
        self.incognito = incognito
        if not incognito:
            self.db_path = os.path.expanduser("~/.browser_data.db")
            self.connect()
            self.create_tables()
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
            
            if self.conn:
                self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
    
    def add_visit(self, url, title):
        if self.incognito or not self.cursor or not self.conn:
            return False
        
        try:
            # Get domain and IP
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            if not domain:
                return False
            
            try:
                ip_address = socket.gethostbyname(domain)
            except:
                ip_address = "Unknown"
            
            # Add to database
            self.cursor.execute(
                "INSERT INTO visits (url, title, ip_address) VALUES (?, ?, ?)",
                (url, title, ip_address)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording visit: {e}")
            return False
    
    def get_recent_visits(self, limit=20):
        if self.incognito or not self.cursor:
            return []
        
        try:
            self.cursor.execute(
                "SELECT url, title, ip_address, visit_time FROM visits ORDER BY visit_time DESC LIMIT ?",
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
            
        if not self.cursor or not self.conn:
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
            
        if not self.cursor or not self.conn:
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
        if self.incognito or not self.cursor or not self.conn:
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
        if self.incognito or not self.cursor or not self.conn:
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
        if self.incognito or not self.cursor or not self.conn:
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

class HTMLTextExtractor(HTMLParser):
    """Extract readable text and links from HTML"""
    
    def __init__(self):
        super().__init__()
        self.result = []
        self.links = []
        self.current_link = None
        self.skip_data = False
        self.in_title = False
        self.title = None
        self.in_body = False
        self.ignore_tags = ['script', 'style', 'meta', 'head', 'svg', 'path']
    
    def handle_starttag(self, tag, attrs):
        # Skip content of ignored tags
        if tag.lower() in self.ignore_tags:
            self.skip_data = True
            return
        
        # Track if we're in body (for better content extraction)
        if tag.lower() == 'body':
            self.in_body = True
        
        # Track title
        if tag.lower() == 'title':
            self.in_title = True
        
        # Extract links
        if tag.lower() == 'a':
            href = None
            for attr in attrs:
                if attr[0].lower() == 'href':
                    href = attr[1]
                    break
            
            if href:
                link_id = len(self.links) + 1
                self.links.append((link_id, href))
                self.current_link = link_id
                self.result.append(f"\033[34m[{link_id}]\033[0m ")  # Blue link indicators
    
    def handle_endtag(self, tag):
        if tag.lower() in self.ignore_tags:
            self.skip_data = False
        
        if tag.lower() == 'a':
            self.current_link = None
        
        if tag.lower() == 'title':
            self.in_title = False
        
        # Add line breaks for block elements
        if tag.lower() in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            self.result.append('\n')
        
        if tag.lower() in ['br']:
            self.result.append('\n')
    
    def handle_data(self, data):
        if self.skip_data:
            return
        
        # Track title
        if self.in_title and not self.title:
            self.title = data.strip()
        
        # Only process non-empty data
        text = data.strip()
        if text:
            self.result.append(text)

class ConsoleBrowser:
    def __init__(self):
        self.history = []
        self.current_index = -1
        self.default_url = "https://www.google.com"
        self.incognito_mode = False
        self.dark_mode = False
        self.db_manager = DatabaseManager(incognito=self.incognito_mode)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.should_exit = False
        self.load_settings()
        self.current_content = None
        self.current_parser = None
        self.current_title = None
        self.current_url = None
    
    def load_settings(self):
        """Load saved settings"""
        # Dark mode
        self.dark_mode = self.db_manager.get_setting("dark_mode", "0") == "1"
        
        # Apply dark mode if enabled
        if self.dark_mode:
            os.system('color 0F' if os.name == 'nt' else '')
    
    def fetch_url(self, url):
        """Fetch content from a URL"""
        # Handle search queries
        if ' ' in url and '.' not in url:
            search_term = quote_plus(url)
            url = f"https://www.google.com/search?q={search_term}"
        
        # Make sure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check if blocked
        if self.db_manager.is_domain_blocked(url):
            print("\033[91mThis website is blocked by your firewall settings.\033[0m")
            return None, None
        
        try:
            # Fetch content using urllib (more reliable)
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                final_url = response.geturl()
            
            # Add to history
            if self.current_index < len(self.history) - 1:
                self.history = self.history[:self.current_index + 1]
                
            self.history.append(final_url)
            self.current_index = len(self.history) - 1
            
            # Parse content
            parser = HTMLTextExtractor()
            parser.feed(content)
            
            # Store current page data
            self.current_content = content
            self.current_parser = parser
            self.current_title = parser.title or urlparse(url).netloc
            self.current_url = final_url
            
            # Add visit to database if not in incognito mode
            if not self.incognito_mode:
                self.db_manager.add_visit(final_url, parser.title or "")
            
            # Get domain info
            parsed_url = urlparse(final_url)
            domain = parsed_url.netloc
            
            try:
                ip_address = socket.gethostbyname(domain)
                print(f"\033[90mConnected to: {domain} ({ip_address})\033[0m")
            except:
                print(f"\033[90mConnected to: {domain}\033[0m")
            
            return parser, content
        except Exception as e:
            print(f"\033[91mError loading page: {e}\033[0m")
            return None, None
    
    def extract_search_results(self, html_content, url):
        """Extract and display search results from major search engines"""
        if 'google.com/search' in url:
            # Extract Google search results
            results = []
            
            # Pattern for Google search results
            result_blocks = re.findall(r'<div class="g">(.*?)</div>\s*</div>\s*</div>', html_content, re.DOTALL)
            if not result_blocks:
                result_blocks = re.findall(r'<div class="tF2Cxc">(.*?)</div>\s*</div>', html_content, re.DOTALL)
            
            for i, block in enumerate(result_blocks[:10], 1):
                # Extract title
                title_match = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
                title = "No title" if not title_match else re.sub(r'<.*?>', '', title_match.group(1))
                
                # Extract URL
                url_match = re.search(r'<a href="([^"]+)"', block)
                url = "#" if not url_match else url_match.group(1)
                if url.startswith('/url?'):
                    url_param = re.search(r'url=([^&]+)', url)
                    if url_param:
                        url = url_param.group(1)
                
                # Extract snippet
                snippet_match = re.search(r'<div class="[^"]*?"[^>]*?>(.*?)</div>', block, re.DOTALL)
                snippet = "" if not snippet_match else re.sub(r'<.*?>', '', snippet_match.group(1))
                
                results.append({
                    'id': i,
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
            
            # Display results
            print("\n\033[1;32m=== Google Search Results ===\033[0m\n")
            for result in results:
                print(f"\033[1;34m[{result['id']}] {result['title']}\033[0m")
                print(f"\033[90m{result['url']}\033[0m")
                print(f"{result['snippet']}\n")
            
            # Store links for selection
            self.current_parser = HTMLTextExtractor()
            self.current_parser.links = [(r['id'], r['url']) for r in results]
            
            return True
        
        return False
    
    def render_page(self, parser, content, url):
        """Render page content in console"""
        # Check if this is a search results page
        if self.extract_search_results(content, url):
            return
        
        # If not a search page, display the parsed content
        if parser and parser.title:
            print(f"\n\033[1;32m=== {parser.title} ===\033[0m\n")
        
        # Display the content
        print(''.join(parser.result))
        
        # Show available links
        if parser.links:
            print("\n\033[1;33m=== Available Links ===\033[0m")
            for link_id, link_url in parser.links:
                # Truncate very long URLs
                display_url = link_url[:70] + "..." if len(link_url) > 70 else link_url
                print(f"\033[34m[{link_id}]\033[0m {display_url}")
    
    def go_back(self):
        """Go back in history"""
        if self.current_index > 0:
            self.current_index -= 1
            url = self.history[self.current_index]
            parser, content = self.fetch_url(url)
            if parser and content:
                self.render_page(parser, content, url)
        else:
            print("\033[91mCan't go back any further.\033[0m")
    
    def go_forward(self):
        """Go forward in history"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            url = self.history[self.current_index]
            parser, content = self.fetch_url(url)
            if parser and content:
                self.render_page(parser, content, url)
        else:
            print("\033[91mCan't go forward any further.\033[0m")
    
    def add_bookmark(self):
        """Add current page to bookmarks"""
        if not self.current_url or not self.current_title:
            print("\033[91mNo page to bookmark.\033[0m")
            return
        
        if self.db_manager.add_bookmark(self.current_url, self.current_title):
            print(f"\033[92mBookmark added: {self.current_title}\033[0m")
        else:
            print("\033[91mFailed to add bookmark.\033[0m")
    
    def show_bookmarks(self):
        """Show all bookmarks"""
        bookmarks = self.db_manager.get_bookmarks()
        
        if not bookmarks:
            print("\033[91mNo bookmarks found.\033[0m")
            return
        
        print("\n\033[1;32m=== Bookmarks ===\033[0m\n")
        for i, bookmark in enumerate(bookmarks, 1):
            title = bookmark['title'] or bookmark['url']
            print(f"\033[34m[{i}]\033[0m {title}")
            print(f"\033[90m    {bookmark['url']}\033[0m")
        
        # Allow selection
        try:
            choice = input("\nEnter number to open bookmark (or press Enter to cancel): ")
            if choice.strip() and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(bookmarks):
                    url = bookmarks[index]['url']
                    parser, content = self.fetch_url(url)
                    if parser and content:
                        self.render_page(parser, content, url)
        except (ValueError, IndexError):
            print("\033[91mInvalid selection.\033[0m")
    
    def show_history(self):
        """Show browsing history"""
        visits = self.db_manager.get_recent_visits()
        
        if not visits:
            print("\033[91mNo history found.\033[0m")
            return
        
        print("\n\033[1;32m=== Recent History ===\033[0m\n")
        for i, visit in enumerate(visits, 1):
            title = visit['title'] or visit['url']
            print(f"\033[34m[{i}]\033[0m {title}")
            print(f"\033[90m    {visit['url']} - IP: {visit['ip_address']} - {visit['visit_time']}\033[0m")
        
        # Allow selection
        try:
            choice = input("\nEnter number to open page (or press Enter to cancel): ")
            if choice.strip() and choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(visits):
                    url = visits[index]['url']
                    parser, content = self.fetch_url(url)
                    if parser and content:
                        self.render_page(parser, content, url)
        except (ValueError, IndexError):
            print("\033[91mInvalid selection.\033[0m")
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        self.db_manager.save_setting("dark_mode", "1" if self.dark_mode else "0")
        
        if self.dark_mode:
            print("\033[92mDark mode enabled.\033[0m")
            if os.name == 'nt':
                os.system('color 0F')
        else:
            print("\033[92mLight mode enabled.\033[0m")
            if os.name == 'nt':
                os.system('color F0')
    
    def show_firewall(self):
        """Show and manage firewall settings"""
        domains = self.db_manager.get_blocked_domains()
        
        print("\n\033[1;32m=== Firewall Settings ===\033[0m\n")
        
        if domains:
            print("Blocked domains:")
            for i, domain in enumerate(domains, 1):
                print(f"\033[34m[{i}]\033[0m {domain}")
        else:
            print("No domains are currently blocked.")
        
        print("\nFirewall Options:")
        print("[b] Block a new domain")
        print("[u] Unblock a domain")
        print("[x] Return to browser")
        
        choice = input("\nEnter option: ").lower()
        
        if choice == 'b':
            domain = input("Enter domain to block (e.g., example.com): ").strip()
            if domain:
                # Format domain
                if "://" in domain:
                    parsed = urlparse(domain)
                    domain = parsed.netloc
                
                if domain:
                    if self.db_manager.block_domain(domain):
                        print(f"\033[92mDomain '{domain}' has been blocked.\033[0m")
                    else:
                        print("\033[91mFailed to block domain.\033[0m")
                else:
                    print("\033[91mInvalid domain.\033[0m")
        
        elif choice == 'u':
            if domains:
                domain_num = input("Enter number of domain to unblock: ")
                if domain_num.isdigit():
                    index = int(domain_num) - 1
                    if 0 <= index < len(domains):
                        domain = domains[index]
                        if self.db_manager.unblock_domain(domain):
                            print(f"\033[92mDomain '{domain}' has been unblocked.\033[0m")
                        else:
                            print("\033[91mFailed to unblock domain.\033[0m")
                    else:
                        print("\033[91mInvalid selection.\033[0m")
                else:
                    print("\033[91mInvalid input.\033[0m")
            else:
                print("\033[91mNo domains to unblock.\033[0m")
    
    def open_in_default_browser(self):
        """Open current URL in system's default browser"""
        if not self.current_url:
            print("\033[91mNo URL to open.\033[0m")
            return
        
        try:
            webbrowser.open(self.current_url)
            print(f"\033[92mOpened in default browser: {self.current_url}\033[0m")
        except Exception as e:
            print(f"\033[91mError opening browser: {e}\033[0m")
    
    def toggle_incognito(self):
        """Toggle incognito mode"""
        self.incognito_mode = not self.incognito_mode
        self.db_manager = DatabaseManager(incognito=self.incognito_mode)
        
        if self.incognito_mode:
            print("\033[92mIncognito mode enabled. Your browsing history will not be saved.\033[0m")
        else:
            print("\033[92mNormal browsing mode. Your browsing history will be saved.\033[0m")
    
    def show_help(self):
        """Show help information"""
        print("\n\033[1;32m=== Browser Help ===\033[0m\n")
        print("Enter a URL or search terms to browse.")
        print("\nCommands:")
        print("  [number]   : Follow link with that number")
        print("  back       : Go back in history")
        print("  forward    : Go forward in history")
        print("  refresh    : Reload current page")
        print("  bookmark   : Add current page to bookmarks")
        print("  bookmarks  : Show all bookmarks")
        print("  history    : Show browsing history")
        print("  firewall   : Manage firewall settings")
        print("  dark       : Toggle dark mode")
        print("  incognito  : Toggle incognito mode")
        print("  open       : Open current page in default browser")
        print("  help       : Show this help")
        print("  exit/quit  : Exit browser")
    
    def main_loop(self):
        """Main browser loop"""
        print("\n\033[1;32m=== Console Web Browser ===\033[0m")
        print("Type 'help' for commands or enter a URL to begin.\n")
        
        # Start with Google
        parser, content = self.fetch_url(self.default_url)
        if parser and content:
            self.render_page(parser, content, self.default_url)
        
        # Main loop
        while not self.should_exit:
            print("\n\033[1;36m" + ("🕵️ " if self.incognito_mode else "") + "Enter URL, search, or command:\033[0m", end=" ")
            command = input().strip()
            
            if not command:
                continue
            
            # Handle commands
            if command.lower() in ['exit', 'quit']:
                self.should_exit = True
            
            elif command.lower() == 'help':
                self.show_help()
            
            elif command.lower() == 'back':
                self.go_back()
            
            elif command.lower() == 'forward':
                self.go_forward()
            
            elif command.lower() == 'refresh' and self.current_url:
                parser, content = self.fetch_url(self.current_url)
                if parser and content:
                    self.render_page(parser, content, self.current_url)
            
            elif command.lower() == 'bookmark':
                self.add_bookmark()
            
            elif command.lower() == 'bookmarks':
                self.show_bookmarks()
            
            elif command.lower() == 'history':
                self.show_history()
            
            elif command.lower() == 'dark':
                self.toggle_dark_mode()
            
            elif command.lower() == 'incognito':
                self.toggle_incognito()
            
            elif command.lower() == 'firewall':
                self.show_firewall()
            
            elif command.lower() == 'open':
                self.open_in_default_browser()
            
            elif command.isdigit() and self.current_parser:
                # Follow a link
                link_id = int(command)
                for id, url in self.current_parser.links:
                    if id == link_id:
                        parser, content = self.fetch_url(url)
                        if parser and content:
                            self.render_page(parser, content, url)
                        break
                else:
                    print(f"\033[91mNo link with ID {link_id}.\033[0m")
            
            else:
                # Treat as URL or search term
                parser, content = self.fetch_url(command)
                if parser and content:
                    self.render_page(parser, content, command)
        
        # Clean up
        self.db_manager.close()
        print("\n\033[1;32mThank you for using Console Web Browser!\033[0m")

if __name__ == "__main__":
    browser = ConsoleBrowser()
    try:
        browser.main_loop()
    except KeyboardInterrupt:
        print("\n\033[1;32mExiting browser...\033[0m")
        browser.db_manager.close()
    except Exception as e:
        print(f"\n\033[91mAn error occurred: {e}\033[0m")
        browser.db_manager.close()