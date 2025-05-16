#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from browser import Browser

if __name__ == "__main__":
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ModernBrowser")
    app.setOrganizationName("ModernBrowser")
    app.setOrganizationDomain("modernbrowser.org")
    
    # Initialize and show the browser
    browser = Browser()
    browser.show()
    
    # Start the event loop
    sys.exit(app.exec())
