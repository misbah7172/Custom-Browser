from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeyEvent

class AddressBar(QLineEdit):
    """Address bar for entering and displaying URLs"""
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        
        # Set placeholder text
        self.setPlaceholderText("Enter URL or search terms...")
        
        # Connect to returnPressed signal for URL navigation
        self.returnPressed.connect(self.navigate_to_url)
        
        # Set initial size policy
        self.setSizePolicy(
            QLineEdit.SizePolicy.Expanding,
            QLineEdit.SizePolicy.Fixed
        )
        self.setMinimumHeight(30)
    
    def navigate_to_url(self):
        """Navigate to the URL entered in the address bar"""
        url_text = self.text().strip()
        
        # If empty, do nothing
        if not url_text:
            return
        
        # Check if input looks like a search query
        if " " in url_text or "." not in url_text:
            # Format as a Google search
            search_url = f"https://www.google.com/search?q={url_text.replace(' ', '+')}"
            self.browser.navigate_to_url(search_url)
        else:
            # Navigate directly to the URL
            self.browser.navigate_to_url(url_text)

    def keyPressEvent(self, event):
        """Handle additional keyboard events for the address bar"""
        # Escape key clears focus
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        # Default handling for other keys
        else:
            super().keyPressEvent(event)
