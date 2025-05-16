#!/usr/bin/env python3
"""
Simple script to start the web browser based on available libraries
"""
import os
import sys
import subprocess
import platform

def main():
    """Check system compatibility and launch appropriate browser"""
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check operating system
    system = platform.system()
    print(f"Operating system: {system}")
    
    # Try importing PyQt6
    try:
        import PyQt6
        print("PyQt6 found, checking WebEngine...")
        
        try:
            from PyQt6 import QtWebEngineWidgets
            print("QtWebEngine available, launching GUI browser...")
            
            # Launch browser directly
            if system == "Windows":
                os.system("start pythonw web_browser.py")
            else:
                os.system("python web_browser.py &")
            
            print("Browser launched!")
            return
        except ImportError:
            print("QtWebEngine not available")
    except ImportError:
        print("PyQt6 not available")
    
    # If we can't launch the GUI version, try to find a suitable alternative
    if system == "Windows":
        # On Windows, try to launch in default browser
        print("Opening in system default browser...")
        os.system("start https://www.google.com")
    elif system == "Darwin":  # macOS
        print("Opening in system default browser...")
        os.system("open https://www.google.com")
    elif system == "Linux":
        # Try common browsers
        browsers = ["google-chrome", "firefox", "chromium-browser", "brave-browser"]
        for browser in browsers:
            try:
                subprocess.run(["which", browser], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Found {browser}, launching...")
                subprocess.Popen([browser, "https://www.google.com"])
                return
            except subprocess.CalledProcessError:
                continue
        
        # No browser found, try xdg-open
        try:
            subprocess.Popen(["xdg-open", "https://www.google.com"])
            print("Opened in default browser using xdg-open")
            return
        except:
            print("Could not launch any browser")
    
    print("\nTo install required libraries, run:")
    print("pip install PyQt6 PyQt6-WebEngine")

if __name__ == "__main__":
    main()