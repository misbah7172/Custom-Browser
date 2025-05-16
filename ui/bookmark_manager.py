from PyQt6.QtWidgets import (
    QWidget, QToolBar, QPushButton, QMenu, QAction,
    QVBoxLayout, QHBoxLayout, QDialog, QLabel,
    QLineEdit, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon
import json
import os

class BookmarkManager(QWidget):
    """Manages browser bookmarks"""
    
    bookmark_selected = pyqtSignal(QUrl)
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.bookmarks = []
        self.bookmark_file = os.path.expanduser("~/.modern_browser_bookmarks.json")
        
        # Load existing bookmarks
        self.load_bookmarks()
        
        # Setup UI components
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the bookmark manager UI"""
        layout = QVBoxLayout(self)
        
        # Bookmark toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        
        # Add bookmark button
        self.add_bookmark_button = QPushButton("Add Bookmark")
        self.add_bookmark_button.clicked.connect(self.add_current_page_bookmark)
        
        # Bookmark list
        self.bookmark_list = QListWidget()
        self.bookmark_list.itemClicked.connect(self.on_bookmark_clicked)
        
        # Populate bookmark list
        self.update_bookmark_list()
        
        # Add components to layout
        layout.addWidget(self.add_bookmark_button)
        layout.addWidget(self.bookmark_list)
    
    def load_bookmarks(self):
        """Load bookmarks from file"""
        try:
            if os.path.exists(self.bookmark_file):
                with open(self.bookmark_file, 'r') as f:
                    self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = []
    
    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            with open(self.bookmark_file, 'w') as f:
                json.dump(self.bookmarks, f)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def update_bookmark_list(self):
        """Update the bookmark list widget"""
        self.bookmark_list.clear()
        for bookmark in self.bookmarks:
            item = QListWidgetItem(bookmark['title'])
            item.setData(Qt.ItemDataRole.UserRole, bookmark['url'])
            self.bookmark_list.addItem(item)
    
    def add_current_page_bookmark(self):
        """Add the current page as a bookmark"""
        current_tab = self.browser.tabs.currentWidget()
        if current_tab:
            title = current_tab.title()
            url = current_tab.url().toString()
            
            # Check if already bookmarked
            for bookmark in self.bookmarks:
                if bookmark['url'] == url:
                    return
            
            # Add new bookmark
            self.bookmarks.append({
                'title': title,
                'url': url
            })
            
            # Save and update
            self.save_bookmarks()
            self.update_bookmark_list()
    
    def on_bookmark_clicked(self, item):
        """Handle bookmark selection"""
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.bookmark_selected.emit(QUrl(url))
