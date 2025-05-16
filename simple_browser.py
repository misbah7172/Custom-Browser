#!/usr/bin/env python3
"""
Simple browser without WebEngine dependency, but with tracking and firewall features
"""
import sys
import os
import socket
import urllib.request
import urllib.parse
import re
import html
from urllib.error import URLError, HTTPError

# Database Manager
from db_manager import DatabaseManager

class SimpleBrowser:
    """Simple browser with tracking and security features"""
    
    def __init__(self):
        # Initialize database manager
        self.db_manager = DatabaseManager()
        self.current_url = None
        self.history = []
        self.history_position = -1
        
        self.show_welcome()
        self.main_loop()
    
    def show_welcome(self):
        """Display welcome message"""
        print("\n" + "="*60)
        print(" SIMPLE BROWSER WITH TRACKING & SECURITY ".center(60, "="))
        print("="*60)
        print("\nCommands:")
        print("  - open [url]           - Open a website")
        print("  - back                 - Go back in history")
        print("  - forward              - Go forward in history")
        print("  - firewall             - Manage firewall settings")
        print("  - block [domain]       - Block a domain")
        print("  - unblock [domain]     - Unblock a domain")
        print("  - blocklist            - Show blocked domains")
        print("  - history              - Show browsing history with IPs")
        print("  - exit                 - Exit the browser")
        print("\nDefault search is Google")
        print("="*60)
    
    def navigate_to_url(self, url):
        """Navigate to a URL with tracking and firewall checks"""
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
        
        # Get domain info
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        try:
            # Get IP address
            ip_address = socket.gethostbyname(domain)
            print(f"\nConnecting to: {domain} ({ip_address})")
            
            # Fetch the URL
            print(f"Loading {url}...")
            try:
                response = urllib.request.urlopen(url, timeout=10)
                
                # Get content type
                content_type = response.getheader('Content-Type', 'unknown')
                
                # Get page content (for HTML pages)
                if 'text/html' in content_type:
                    try:
                        html_content = response.read().decode('utf-8', errors='replace')
                        
                        # Extract title
                        title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                        title = title_match.group(1) if title_match else "No title"
                        title = html.unescape(title.strip())
                        
                        # Save to history
                        if self.history_position < len(self.history) - 1:
                            # Truncate forward history
                            self.history = self.history[:self.history_position + 1]
                        
                        self.history.append(url)
                        self.history_position = len(self.history) - 1
                        self.current_url = url
                        
                        # Save visit to database with IP
                        self.db_manager.add_visit(url, title, ip_address)
                        
                        # Display page info
                        print("\n" + "="*60)
                        print(f"URL: {url}")
                        print(f"Title: {title}")
                        print(f"Server IP: {ip_address}")
                        print("="*60)
                        
                    except Exception as e:
                        print(f"Error parsing content: {e}")
                        self.db_manager.add_visit(url, "Error: Content parsing failed", ip_address)
                
                else:
                    print(f"\nContent type is {content_type}, not displaying")
                    self.db_manager.add_visit(url, "Non-HTML content", ip_address)
                    
                    # Save to history
                    if self.history_position < len(self.history) - 1:
                        self.history = self.history[:self.history_position + 1]
                    
                    self.history.append(url)
                    self.history_position = len(self.history) - 1
                    self.current_url = url
                
            except HTTPError as e:
                print(f"HTTP Error: {e.code} - {e.reason}")
                self.db_manager.add_visit(url, f"Error: {e.code}", ip_address)
            
            except URLError as e:
                print(f"URL Error: {e.reason}")
                self.db_manager.add_visit(url, f"Error: {str(e)}", ip_address)
        
        except socket.gaierror:
            print(f"Could not resolve domain: {domain}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def show_history(self):
        """Show browsing history with tracking info"""
        visits = self.db_manager.get_recent_visits()
        
        if not visits:
            print("No browsing history available")
            return
        
        print("\n=== Browsing History with Tracking ===")
        for i, visit in enumerate(visits, 1):
            url = visit['url']
            title = visit['title'] or url
            ip = visit['ip_address']
            location = visit['location']
            timestamp = visit['visit_time']
            
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   IP Address: {ip}")
            print(f"   Location: {location}")
            print(f"   Time: {timestamp}")
            print()
    
    def go_back(self):
        """Navigate back in history"""
        if self.history_position > 0:
            self.history_position -= 1
            print(f"Going back to: {self.history[self.history_position]}")
            self.current_url = self.history[self.history_position]
        else:
            print("No previous page in history")
    
    def go_forward(self):
        """Navigate forward in history"""
        if self.history_position < len(self.history) - 1:
            self.history_position += 1
            print(f"Going forward to: {self.history[self.history_position]}")
            self.current_url = self.history[self.history_position]
        else:
            print("No next page in history")
    
    def manage_firewall(self):
        """Manage firewall settings"""
        print("\n=== Firewall Settings ===")
        print("1. View blocked domains")
        print("2. Block a domain")
        print("3. Unblock a domain")
        print("4. Back to main menu")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            self.show_blocklist()
        elif choice == '2':
            domain = input("Enter domain to block: ")
            self.block_domain(domain)
        elif choice == '3':
            domain = input("Enter domain to unblock: ")
            self.unblock_domain(domain)
        elif choice == '4':
            return
        else:
            print("Invalid choice")
    
    def block_domain(self, domain):
        """Block a domain"""
        if not domain:
            print("Please specify a domain to block")
            return
        
        # Clean up domain
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
        """Unblock a domain"""
        if not domain:
            print("Please specify a domain to unblock")
            return
        
        # Clean up domain
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
        """Show blocked domains"""
        domains = self.db_manager.get_blocked_domains()
        
        if not domains:
            print("No domains are currently blocked")
            return
        
        print("\n=== Blocked Domains ===")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain}")
    
    def main_loop(self):
        """Main browser loop"""
        while True:
            try:
                command = input("\nbrowser> ").strip()
                
                if not command:
                    continue
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if cmd in ['exit', 'quit']:
                    break
                
                elif cmd == 'open':
                    if arg:
                        self.navigate_to_url(arg)
                    else:
                        print("Please provide a URL to open")
                
                elif cmd == 'back':
                    self.go_back()
                
                elif cmd == 'forward':
                    self.go_forward()
                
                elif cmd == 'history':
                    self.show_history()
                
                elif cmd == 'firewall':
                    self.manage_firewall()
                
                elif cmd == 'block':
                    self.block_domain(arg)
                
                elif cmd == 'unblock':
                    self.unblock_domain(arg)
                
                elif cmd == 'blocklist':
                    self.show_blocklist()
                
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'open [url]' to navigate or 'exit' to quit")
            
            except KeyboardInterrupt:
                print("\nKeyboard interrupt. Type 'exit' to quit.")
            
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print("Browser closed.")
        self.db_manager.close()

if __name__ == "__main__":
    SimpleBrowser()