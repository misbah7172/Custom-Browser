#!/usr/bin/env python3
"""
Console-based browser implementation with tracking and security features
"""
import sys
import os
import re
import socket
import sqlite3
import urllib.parse
import urllib.request
import datetime
import html
import json
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

class DatabaseManager:
    """Manages website visit tracking and firewall settings"""
    
    def __init__(self):
        """Initialize the database"""
        self.db_path = os.path.expanduser("~/.browser_tracker.db")
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        # List of blocked domains
        self.blocked_domains = self.get_blocked_domains()
    
    def connect(self):
        """Connect to the SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        # Table for visited websites
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
        
        # Table for blocked domains (firewall)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS firewall (
                id INTEGER PRIMARY KEY,
                domain TEXT UNIQUE NOT NULL,
                reason TEXT,
                blocked_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_visit(self, url, title=None):
        """Record a website visit with its IP address and location"""
        try:
            # Parse domain from URL
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            
            # Skip about:blank and empty URLs
            if not domain or domain == "about:blank":
                return False
                
            # Get IP address (if possible)
            try:
                ip_address = socket.gethostbyname(domain)
            except:
                ip_address = "Unknown"
            
            # In a real implementation, we would use a geolocation service
            # For now, just set a placeholder
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
        """Check if a domain is blocked by the firewall"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            
            # Check domain against blocked list
            for blocked_domain in self.blocked_domains:
                if domain == blocked_domain or domain.endswith("." + blocked_domain):
                    return True
            
            return False
        except:
            return False
    
    def get_blocked_domains(self):
        """Retrieve the list of blocked domains"""
        try:
            self.cursor.execute("SELECT domain FROM firewall")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving blocked domains: {e}")
            return []
    
    def block_domain(self, domain, reason="Manually blocked"):
        """Add a domain to the blocklist"""
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO firewall (domain, reason) VALUES (?, ?)",
                (domain, reason)
            )
            self.conn.commit()
            # Update the cached blocked domains
            self.blocked_domains = self.get_blocked_domains()
            return True
        except Exception as e:
            print(f"Error blocking domain: {e}")
            return False
    
    def unblock_domain(self, domain):
        """Remove a domain from the blocklist"""
        try:
            self.cursor.execute("DELETE FROM firewall WHERE domain = ?", (domain,))
            self.conn.commit()
            # Update the cached blocked domains
            self.blocked_domains = self.get_blocked_domains()
            return True
        except Exception as e:
            print(f"Error unblocking domain: {e}")
            return False
    
    def get_recent_visits(self, limit=20):
        """Get recent website visits"""
        try:
            self.cursor.execute(
                "SELECT url, title, ip_address, location, visit_time FROM visits ORDER BY visit_time DESC LIMIT ?", 
                (limit,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error retrieving visits: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


class ConsoleBrowser:
    """Simple console-based browser with website tracking and firewall"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.current_url = None
        self.history = []
        self.history_position = -1
        self.show_welcome()
    
    def show_welcome(self):
        """Display welcome message with instructions"""
        print("\n" + "="*60)
        print(" CONSOLE WEB BROWSER WITH TRACKING & FIREWALL ".center(60, "="))
        print("="*60)
        print("\nCommands:")
        print("  open [url]      - Navigate to a URL")
        print("  back            - Go back in history")
        print("  forward         - Go forward in history")
        print("  history         - Show browsing history")
        print("  block [domain]  - Block a domain")
        print("  unblock [domain]- Unblock a domain")
        print("  blocklist       - Show blocked domains")
        print("  visits          - Show visit history with IPs")
        print("  exit/quit       - Exit the browser")
        print("\nDefault search is Google")
        print("="*60 + "\n")
    
    def navigate_to_url(self, url):
        """Navigate to the specified URL and track the visit"""
        # Prepare URL
        if not url.startswith(('http://', 'https://')):
            if ' ' in url or '.' not in url:  # Likely a search query
                url = f"https://www.google.com/search?q={urllib.parse.quote(url)}"
            else:
                url = 'http://' + url
        
        # Check if domain is blocked
        if self.db_manager.is_domain_blocked(url):
            print(f"\n❌ Access Blocked: Domain in the URL is blocked by firewall settings")
            return
        
        # Display information about connection
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        try:
            ip_address = socket.gethostbyname(domain)
            print(f"\nConnecting to: {domain} ({ip_address})")
        except socket.gaierror:
            print(f"\nCould not resolve domain: {domain}")
            return
        
        # Attempt to fetch the URL
        try:
            print(f"Loading {url}...")
            response = urllib.request.urlopen(url, timeout=10)
            
            content_type = response.getheader('Content-Type', 'unknown')
            encoding = 'utf-8'
            
            # Extract encoding if specified
            if 'charset=' in content_type:
                encoding = content_type.split('charset=')[1].split(';')[0]
            
            # If it's HTML, display simplified content
            if 'text/html' in content_type:
                html_content = response.read().decode(encoding, errors='replace')
                
                # Extract title
                title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1) if title_match else "No title"
                title = html.unescape(title.strip())
                
                # Save to history
                if self.history_position < len(self.history) - 1:
                    # If we navigated from a back state, truncate forward history
                    self.history = self.history[:self.history_position + 1]
                
                self.history.append(url)
                self.history_position = len(self.history) - 1
                self.current_url = url
                
                # Record visit with IP address
                self.db_manager.add_visit(url, title)
                
                # Display page info
                print("\n" + "="*60)
                print(f"URL: {url}")
                print(f"Title: {title}")
                print(f"Server IP: {ip_address}")
                print("="*60)
                
                # Extract and display links
                links = re.findall('<a\\s+href="([^"]+)"[^>]*>([^<]+)</a>', html_content)
                if links:
                    print("\nLinks on page:")
                    shown_links = 0
                    for i, (link_url, link_text) in enumerate(links[:10], 1):
                        # Make relative links absolute
                        if link_url.startswith('/'):
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            link_url = base_url + link_url
                        elif not link_url.startswith(('http://', 'https://')):
                            if self.current_url:
                                link_url = urllib.parse.urljoin(self.current_url, link_url)
                        
                        print(f"  {i}. {link_text.strip()}: {link_url}")
                        shown_links += 1
                        if shown_links >= 10:
                            break
                    
                    if len(links) > 10:
                        print(f"  ... and {len(links) - 10} more links")
                
            else:
                print(f"\nContent type is {content_type}, not displaying content")
                print(f"URL: {url}")
                print(f"Server IP: {ip_address}")
                
                # Record visit
                self.db_manager.add_visit(url, "Binary or non-HTML content")
                
                # Save to history
                if self.history_position < len(self.history) - 1:
                    self.history = self.history[:self.history_position + 1]
                
                self.history.append(url)
                self.history_position = len(self.history) - 1
                self.current_url = url
            
        except HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            # Still record the visit with the error
            self.db_manager.add_visit(url, f"Error: {e.code}")
        
        except URLError as e:
            print(f"URL Error: {e.reason}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def go_back(self):
        """Navigate back in history"""
        if self.history_position > 0:
            self.history_position -= 1
            print(f"Going back to: {self.history[self.history_position]}")
            # We don't call navigate_to_url to avoid adding duplicate history entries
            self.current_url = self.history[self.history_position]
            print(f"Current URL: {self.current_url}")
        else:
            print("No previous page in history")
    
    def go_forward(self):
        """Navigate forward in history"""
        if self.history_position < len(self.history) - 1:
            self.history_position += 1
            print(f"Going forward to: {self.history[self.history_position]}")
            self.current_url = self.history[self.history_position]
            print(f"Current URL: {self.current_url}")
        else:
            print("No next page in history")
    
    def show_history(self):
        """Display browsing history"""
        if not self.history:
            print("No browsing history")
            return
        
        print("\n--- Browsing History ---")
        for i, url in enumerate(self.history):
            marker = " ➤" if i == self.history_position else ""
            print(f"{i+1}. {url}{marker}")
    
    def block_domain(self, domain):
        """Add a domain to the firewall blocklist"""
        if not domain:
            print("Please specify a domain to block")
            return
        
        # Clean up the domain
        if domain.startswith(('http://', 'https://')):
            parsed = urllib.parse.urlparse(domain)
            domain = parsed.netloc
        
        if not domain:
            print("Invalid domain format")
            return
        
        if self.db_manager.block_domain(domain):
            print(f"Domain '{domain}' has been blocked")
        else:
            print(f"Failed to block domain '{domain}'")
    
    def unblock_domain(self, domain):
        """Remove a domain from the firewall blocklist"""
        if not domain:
            print("Please specify a domain to unblock")
            return
        
        # Clean up the domain
        if domain.startswith(('http://', 'https://')):
            parsed = urllib.parse.urlparse(domain)
            domain = parsed.netloc
        
        if not domain:
            print("Invalid domain format")
            return
        
        if self.db_manager.unblock_domain(domain):
            print(f"Domain '{domain}' has been unblocked")
        else:
            print(f"Failed to unblock domain '{domain}' or domain not in blocklist")
    
    def show_blocklist(self):
        """Display the list of blocked domains"""
        domains = self.db_manager.get_blocked_domains()
        if not domains:
            print("No domains are currently blocked")
            return
        
        print("\n--- Blocked Domains ---")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain}")
    
    def show_visits(self):
        """Display the history of visited sites with their details"""
        visits = self.db_manager.get_recent_visits()
        if not visits:
            print("No visit history available")
            return
        
        print("\n--- Recent Website Visits ---")
        for i, visit in enumerate(visits, 1):
            title = visit['title'] or 'No title'
            url = visit['url']
            ip = visit['ip_address']
            location = visit['location']
            timestamp = visit['visit_time']
            
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   IP Address: {ip}")
            print(f"   Location: {location}")
            print(f"   Time: {timestamp}")
            print("")
    
    def run(self):
        """Main browser loop"""
        running = True
        while running:
            try:
                command = input("\nbrowser> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if cmd in ["exit", "quit"]:
                    running = False
                
                elif cmd == "open":
                    if arg:
                        self.navigate_to_url(arg)
                    else:
                        print("Please provide a URL to open")
                
                elif cmd == "back":
                    self.go_back()
                
                elif cmd == "forward":
                    self.go_forward()
                
                elif cmd == "history":
                    self.show_history()
                
                elif cmd == "block":
                    self.block_domain(arg)
                
                elif cmd == "unblock":
                    self.unblock_domain(arg)
                
                elif cmd == "blocklist":
                    self.show_blocklist()
                
                elif cmd == "visits":
                    self.show_visits()
                
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'open [url]' to navigate, or 'exit' to quit")
            
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received. Type 'exit' to quit.")
            
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Clean up
        self.db_manager.close()
        print("Browser closed. Goodbye!")


if __name__ == "__main__":
    browser = ConsoleBrowser()
    browser.run()