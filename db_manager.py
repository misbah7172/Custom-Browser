"""
Database manager for tracking browser activity
"""
import sqlite3
import os
import socket
import datetime
from urllib.parse import urlparse

class DatabaseManager:
    """Manages website visit tracking and firewall settings"""
    
    def __init__(self):
        """Initialize the database"""
        self.db_path = os.path.expanduser("~/.modern_browser.db")
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        
        # List of blocked domains
        self.blocked_domains = self.get_blocked_domains()
    
    def connect(self):
        """Connect to the SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
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
            parsed_url = urlparse(url)
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
            parsed_url = urlparse(url)
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
        except:
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
    
    def get_recent_visits(self, limit=100):
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