"""
Firewall management UI for blocking malicious websites
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from urllib.parse import urlparse

class FirewallManager(QWidget):
    """UI for managing website blocking rules"""
    
    domain_blocked = pyqtSignal(str)
    domain_unblocked = pyqtSignal(str)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.update_blocked_list()
    
    def setup_ui(self):
        """Set up the UI components"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Firewall Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Block domain input
        block_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("Enter domain to block (e.g., example.com)")
        block_button = QPushButton("Block Domain")
        block_button.clicked.connect(self.block_domain)
        block_layout.addWidget(self.domain_input)
        block_layout.addWidget(block_button)
        layout.addLayout(block_layout)
        
        # List of blocked domains
        layout.addWidget(QLabel("Blocked Domains:"))
        self.blocked_list = QListWidget()
        self.blocked_list.setAlternatingRowColors(True)
        layout.addWidget(self.blocked_list)
        
        # Unblock button
        unblock_button = QPushButton("Unblock Selected")
        unblock_button.clicked.connect(self.unblock_selected)
        layout.addWidget(unblock_button)
    
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
            self.domain_blocked.emit(domain)
            QMessageBox.information(self, "Domain Blocked", f"The domain '{domain}' has been blocked.")
    
    def unblock_selected(self):
        """Unblock the selected domain"""
        selected_items = self.blocked_list.selectedItems()
        if not selected_items:
            return
        
        domain = selected_items[0].text()
        if self.db_manager.unblock_domain(domain):
            self.update_blocked_list()
            self.domain_unblocked.emit(domain)
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
            url, title, ip, location, timestamp = visit
            display_text = f"{title or url} - {ip} - {location} - {timestamp}"
            item = QListWidgetItem(display_text)
            item.setToolTip(url)
            self.visit_list.addItem(item)