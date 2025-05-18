#!/usr/bin/env python3
"""
Main entry point for the browser application
"""
import sys
import os
import platform

def start_browser():
    """Start the most suitable browser based on available dependencies"""
    try:
        # Try importing PyQt6 for GUI browser
        import PyQt6
        print("Starting GUI browser...")
        import web_browser
        app = web_browser.QApplication(sys.argv)
        browser = web_browser.WebBrowser()
        browser.show()
        sys.exit(app.exec())
    except ImportError:
        print("PyQt6 not available. Starting console browser...")
        try:
            # Try using console browser
            import browser_cli
            browser = browser_cli.ConsoleBrowser()
            browser.main_loop()
        except Exception as e:
            print(f"Error starting console browser: {e}")
            print("Attempting to open system browser instead...")
            
            # Fallback to system browser
            import webbrowser
            webbrowser.open("https://www.google.com")

if __name__ == "__main__":
    print(f"Starting browser on {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version.split()[0]}")
    start_browser()