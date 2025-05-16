#!/usr/bin/env python3
"""
Modern browser with dark web capability, tracking, and firewall features
- Supports regular and .onion sites
- Tracks all website visits with IP addresses
- Provides firewall functionality to block domains
- Works with Tor network
"""
import sys
import os
import socket
import socks
import requests
from urllib.parse import urlparse
import re
import html
import time
from datetime import datetime

# Import database manager
from db_manager import DatabaseManager

class TorManager:
    """Manages Tor connections for accessing .onion sites"""
    
    def __init__(self):
        """Initialize Tor manager"""
        self.tor_enabled = False
        self.default_socket = None
    
    def enable_tor(self, tor_port=9050):
        """Enable Tor for requests"""
        if not self.tor_enabled:
            # Backup default socket
            self.default_socket = socket.socket
            
            # Configure requests to use Tor
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", tor_port)
            socket.socket = socks.socksocket
            
            self.tor_enabled = True
            print("Tor routing enabled for dark web access")
            return True
        return False
    
    def disable_tor(self):
        """Disable Tor and restore normal connections"""
        if self.tor_enabled and self.default_socket:
            # Restore original socket
            socket.socket = self.default_socket
            self.tor_enabled = False
            print("Tor routing disabled, using normal connection")
            return True
        return False
    
    def is_tor_running(self, tor_port=9050):
        """Check if Tor is accessible"""
        try:
            # Try connecting to the Tor SOCKS port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(("127.0.0.1", tor_port))
            s.close()
            return True
        except:
            return False
    
    def get_tor_status(self):
        """Get current Tor status"""
        if self.is_tor_running():
            if self.tor_enabled:
                return "Tor is running and enabled for browsing"
            else:
                return "Tor is running but not enabled for browsing"
        else:
            return "Tor is not running on this system"

class ConsoleUI:
    """User interface for console-based browser"""
    
    def __init__(self):
        """Initialize UI components"""
        self.clear_screen()
        self.display_header()
    
    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self):
        """Display browser header"""
        print("\n" + "="*70)
        print(" DARKWEB BROWSER WITH TRACKING & SECURITY ".center(70, "="))
        print("="*70)
    
    def display_help(self):
        """Display help information"""
        print("\nCommands:")
        print("  open [url]                - Navigate to a URL (regular or .onion)")
        print("  tor [on|off|status]       - Enable/disable/check Tor for dark web access")
        print("  back                      - Go back in browsing history")
        print("  forward                   - Go forward in browsing history")
        print("  history                   - Show browsing history")
        print("  block [domain]            - Block a domain")
        print("  unblock [domain]          - Unblock a domain")
        print("  blocklist                 - Show blocked domains")
        print("  visits                    - Show visit history with IPs")
        print("  clear                     - Clear the screen")
        print("  help                      - Show this help message")
        print("  exit/quit                 - Exit the browser")
        print("\nTo access .onion sites, first enable Tor with 'tor on'")
        print("="*70)
    
    def display_page(self, url, title, content, ip=None, status=None):
        """Display a webpage in the console"""
        print("\n" + "="*70)
        print(f"URL: {url}")
        print(f"Title: {title}")
        if ip:
            print(f"Server IP: {ip}")
        if status:
            print(f"Status: {status}")
        print("="*70)
        print("\n" + content)
        print("\n" + "="*70)
    
    def display_error(self, message):
        """Display an error message"""
        print(f"\n❌ Error: {message}")
    
    def display_success(self, message):
        """Display a success message"""
        print(f"\n✅ {message}")
    
    def display_info(self, message):
        """Display an informational message"""
        print(f"\nℹ️ {message}")
    
    def display_warning(self, message):
        """Display a warning message"""
        print(f"\n⚠️ Warning: {message}")
    
    def get_input(self, prompt="browser> "):
        """Get user input"""
        return input(prompt).strip()
    
    def display_visits(self, visits):
        """Display visit history"""
        if not visits:
            print("\nNo visit history available")
            return
        
        print("\n=== Website Visit History ===")
        for i, visit in enumerate(visits, 1):
            try:
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
            except (KeyError, TypeError):
                continue
    
    def display_blocklist(self, domains):
        """Display blocked domains"""
        if not domains:
            print("\nNo domains are currently blocked")
            return
        
        print("\n=== Blocked Domains ===")
        for i, domain in enumerate(domains, 1):
            print(f"{i}. {domain}")

class DarkWebBrowser:
    """Browser with dark web capability and tracking features"""
    
    def __init__(self):
        """Initialize the browser"""
        self.db_manager = DatabaseManager()
        self.ui = ConsoleUI()
        self.tor_manager = TorManager()
        
        self.current_url = None
        self.history = []
        self.history_position = -1
        
        # Show help message
        self.ui.display_help()
    
    def navigate_to_url(self, url):
        """Navigate to a URL (regular or .onion)"""
        # Prepare URL
        if not url.startswith(('http://', 'https://')):
            if ' ' in url or '.' not in url:  # Likely a search query
                url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
            else:
                url = 'http://' + url
        
        # Check if it's a .onion site
        is_onion = url.endswith('.onion') or '.onion/' in url
        
        # If it's an onion site and Tor is not enabled, warn the user
        if is_onion and not self.tor_manager.tor_enabled:
            self.ui.display_warning("This is a .onion site but Tor is not enabled. Enable Tor first with 'tor on'")
            return
        
        # Check if domain is blocked
        if self.db_manager.is_domain_blocked(url):
            self.ui.display_warning("This website has been blocked by firewall settings")
            return
        
        # Display loading message
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        self.ui.display_info(f"Loading {url}...")
        
        try:
            # Get IP address (for non-.onion sites)
            ip_address = "Hidden (Tor Network)" if is_onion else self.get_ip_address(domain)
            
            # Fetch content
            try:
                response = requests.get(url, timeout=10)
                content_type = response.headers.get('content-type', '').lower()
                
                # For HTML content
                if 'text/html' in content_type:
                    html_content = response.text
                    
                    # Extract title
                    title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                    title = title_match.group(1) if title_match else domain
                    title = html.unescape(title.strip())
                    
                    # Extract text content (simplified)
                    text_content = self.extract_text_content(html_content)
                    
                    # Store in history
                    if self.history_position < len(self.history) - 1:
                        # Truncate forward history
                        self.history = self.history[:self.history_position + 1]
                    
                    self.history.append(url)
                    self.history_position = len(self.history) - 1
                    self.current_url = url
                    
                    # Save visit to database
                    self.db_manager.add_visit(url, title)
                    
                    # Display page
                    self.ui.display_page(
                        url=url,
                        title=title,
                        content=text_content,
                        ip=ip_address,
                        status=f"Status: {response.status_code} {response.reason}"
                    )
                else:
                    self.ui.display_info(f"Non-HTML content type: {content_type}")
                    
                    # Still save to history and database
                    if self.history_position < len(self.history) - 1:
                        self.history = self.history[:self.history_position + 1]
                    
                    self.history.append(url)
                    self.history_position = len(self.history) - 1
                    self.current_url = url
                    
                    # Save visit
                    self.db_manager.add_visit(url, f"Non-HTML: {content_type}")
            
            except requests.RequestException as e:
                self.ui.display_error(f"Error fetching page: {str(e)}")
                # Still record the attempted visit
                self.db_manager.add_visit(url, f"Error: {str(e)}")
        
        except Exception as e:
            self.ui.display_error(f"Error: {str(e)}")
    
    def get_ip_address(self, domain):
        """Get IP address for a domain"""
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except:
            return "Unknown"
    
    def extract_text_content(self, html_content, max_length=2000):
        """Extract readable text from HTML (simplified)"""
        # Remove scripts and styles
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Extract text from paragraphs, headings, and other elements
        text_blocks = re.findall(r'<(?:p|h1|h2|h3|h4|h5|h6|div)[^>]*>(.*?)</(?:p|h1|h2|h3|h4|h5|h6|div)>', 
                                html_content, flags=re.DOTALL)
        
        # Clean up the text
        clean_text = []
        for block in text_blocks:
            # Remove HTML tags
            block = re.sub(r'<[^>]*>', '', block)
            # Remove extra whitespace
            block = re.sub(r'\s+', ' ', block).strip()
            if block:
                clean_text.append(block)
        
        # Join and truncate if too long
        result = '\n\n'.join(clean_text)
        if len(result) > max_length:
            result = result[:max_length] + "...\n[Content truncated]"
        
        return result if result else "[No readable text content found]"
    
    def go_back(self):
        """Navigate back in history"""
        if self.history_position > 0:
            self.history_position -= 1
            url = self.history[self.history_position]
            self.ui.display_info(f"Going back to: {url}")
            self.current_url = url
        else:
            self.ui.display_info("No previous page in history")
    
    def go_forward(self):
        """Navigate forward in history"""
        if self.history_position < len(self.history) - 1:
            self.history_position += 1
            url = self.history[self.history_position]
            self.ui.display_info(f"Going forward to: {url}")
            self.current_url = url
        else:
            self.ui.display_info("No next page in history")
    
    def show_history(self):
        """Display browsing history"""
        if not self.history:
            self.ui.display_info("No browsing history")
            return
        
        print("\n--- Browsing History ---")
        for i, url in enumerate(self.history):
            marker = " ➤" if i == self.history_position else ""
            print(f"{i+1}. {url}{marker}")
    
    def block_domain(self, domain):
        """Block a domain"""
        if not domain:
            self.ui.display_error("Please specify a domain to block")
            return
        
        # Clean up domain
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        if not domain:
            self.ui.display_error("Invalid domain format")
            return
        
        if self.db_manager.block_domain(domain):
            self.ui.display_success(f"Domain '{domain}' has been blocked")
        else:
            self.ui.display_error(f"Failed to block domain '{domain}'")
    
    def unblock_domain(self, domain):
        """Unblock a domain"""
        if not domain:
            self.ui.display_error("Please specify a domain to unblock")
            return
        
        # Clean up domain
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        if not domain:
            self.ui.display_error("Invalid domain format")
            return
        
        if self.db_manager.unblock_domain(domain):
            self.ui.display_success(f"Domain '{domain}' has been unblocked")
        else:
            self.ui.display_error(f"Failed to unblock domain '{domain}' or domain not in blocklist")
    
    def manage_tor(self, command):
        """Manage Tor connection"""
        if command == "on":
            if self.tor_manager.is_tor_running():
                if self.tor_manager.enable_tor():
                    self.ui.display_success("Tor routing enabled for dark web access")
                else:
                    self.ui.display_info("Tor is already enabled")
            else:
                self.ui.display_error("Tor is not running on this system. Please install and start Tor first.")
        
        elif command == "off":
            if self.tor_manager.disable_tor():
                self.ui.display_success("Tor routing disabled, using normal connection")
            else:
                self.ui.display_info("Tor is already disabled")
        
        elif command == "status":
            status = self.tor_manager.get_tor_status()
            self.ui.display_info(status)
        
        else:
            self.ui.display_error("Invalid Tor command. Use 'tor on', 'tor off', or 'tor status'")
    
    def run(self):
        """Main browser loop"""
        running = True
        while running:
            try:
                command = self.ui.get_input()
                
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
                        self.ui.display_error("Please provide a URL to open")
                
                elif cmd == "tor":
                    self.manage_tor(arg)
                
                elif cmd == "back":
                    self.go_back()
                
                elif cmd == "forward":
                    self.go_forward()
                
                elif cmd == "history":
                    self.show_history()
                
                elif cmd == "visits":
                    visits = self.db_manager.get_recent_visits()
                    self.ui.display_visits(visits)
                
                elif cmd == "block":
                    self.block_domain(arg)
                
                elif cmd == "unblock":
                    self.unblock_domain(arg)
                
                elif cmd == "blocklist":
                    domains = self.db_manager.get_blocked_domains()
                    self.ui.display_blocklist(domains)
                
                elif cmd == "clear":
                    self.ui.clear_screen()
                    self.ui.display_header()
                
                elif cmd == "help":
                    self.ui.display_help()
                
                else:
                    self.ui.display_error(f"Unknown command: {cmd}")
                    self.ui.display_info("Type 'help' to see available commands")
            
            except KeyboardInterrupt:
                self.ui.display_info("\nKeyboard interrupt received. Type 'exit' to quit.")
            
            except Exception as e:
                self.ui.display_error(f"Error: {str(e)}")
        
        # Clean up
        self.db_manager.close()
        print("Browser closed. Goodbye!")

if __name__ == "__main__":
    browser = DarkWebBrowser()
    browser.run()