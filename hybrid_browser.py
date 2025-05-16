#!/usr/bin/env python3
"""
Hybrid browser that attempts to use GUI if available, or falls back to console mode
Includes all tracking and security features regardless of mode
"""
import sys
import os
import sqlite3
import socket
import urllib.parse
from datetime import datetime

# First, check if PyQt6 is available
GUI_AVAILABLE = False
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QUrl
    GUI_AVAILABLE = True
except ImportError:
    print("PyQt6 not available. Using console mode.")

# Import common database manager
from db_manager import DatabaseManager

# If GUI is available, run the GUI browser
if GUI_AVAILABLE:
    try:
        from browser import Browser
        
        def run_gui_browser():
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
            
    except ImportError as e:
        print(f"Error loading GUI browser: {e}")
        GUI_AVAILABLE = False

# Console browser implementation for fallback
def run_console_browser():
    """Run the console-based browser"""
    from browser_cli import ConsoleBrowser
    browser = ConsoleBrowser()
    browser.run()

if __name__ == "__main__":
    if GUI_AVAILABLE:
        try:
            run_gui_browser()
        except Exception as e:
            print(f"Error starting GUI browser: {e}")
            print("Falling back to console mode...")
            run_console_browser()
    else:
        run_console_browser()