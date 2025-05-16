# Modern Web Browser with Security Features

## Overview
This project implements a web browser with built-in security features, including:

1. **Website Visit Tracking**: Records every website you visit
2. **IP Address Logging**: Captures and stores the IP address of each website's server
3. **Location Tracking**: Identifies the geographic location of websites (placeholder ready for integration)
4. **Personal Firewall**: Block malicious websites by domain name

## Project Structure

The browser has two implementations:

1. **Console-based Browser** (`browser_cli.py`): A text-based browser that works in any environment and implements all tracking and security features.

2. **GUI Browser** (remaining files): A PyQt6-based implementation that requires additional system libraries.

## Using the Console Browser

The console browser is fully functional and includes all requested features:

```
python browser_cli.py
```

### Commands
- `open [url]` - Navigate to a URL or search Google
- `back` - Go back in browsing history
- `forward` - Go forward in browsing history
- `history` - Show your browsing history
- `block [domain]` - Block a domain in the firewall
- `unblock [domain]` - Remove a domain from the blocklist
- `blocklist` - Show all blocked domains
- `visits` - Show history of website visits with their IP addresses
- `exit` or `quit` - Exit the browser

### Security Features

1. **IP Tracking**: When you visit a website, the browser automatically resolves and stores its IP address.

2. **Visit History**: All visits are recorded with:
   - URL
   - Page title (when available)
   - Server IP address
   - Timestamp

3. **Firewall**: You can block domains to prevent access to malicious websites.

## Database

The browser stores all data in an SQLite database at `~/.browser_tracker.db` with two tables:

1. **visits**: Records website visits with IP addresses and locations
2. **firewall**: Stores blocked domains

## Implementation Details

- The browser uses a persistent SQLite database to track all visits
- IP addresses are resolved for each domain visited
- The firewall checks each URL against a blocklist before navigation
- All browsing history is maintained for back/forward navigation

## GUI Implementation 

The full PyQt6 GUI implementation requires additional system libraries. The files are included but may need system dependencies installed to run properly.

To run the GUI version (if dependencies are available):

```
python main.py
```