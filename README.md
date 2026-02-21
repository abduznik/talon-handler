# Talon Handler

Talon Handler is a high-performance, purely algorithmic Python CLI tool designed for Homelab monitoring. It automates service discovery, monitors your local ports, and integrates with Telegram via a secure Ghost Auth bridge.

## Key Features
- Smart Scan: Automatically detects locally bound ports using psutil and maps them to common services (Jellyfin, Plex, Home Assistant, etc.).
- Ghost Auth: Cryptographically secure 6-digit OTP authentication for Telegram without hardcoded chat IDs.
- Monitoring Filter: Interactively toggle which services you want to track.
- Live Dashboard: Automatically generates a Markdown dashboard (talon_dashboard.md) for Homarr or other notebook widgets.
- 3-Strike Alerts: Algorithmic failure detection to prevent notification spam.

## Installation
```bash
git clone https://github.com/abduznik/talon-handler.git
cd talon-handler
pip install -e .
```

## Quick Start: The Headstart Command

The headstart command is your entry point. it initializes your configuration and performs the first service discovery scan.

### 1. Run Headstart
```bash
talon headstart
```

### 2. Discovered Services
Talon will scan your system and display a table of discovered services:
```
+-------+------------------+
| Port  | Mapped Service   |
+-------+------------------+
| 8096  | Jellyfin         |
| 32400 | Plex             |
| 8123  | Home Assistant   |
+-------+------------------+
```

### 3. Ghost Auth
After scanning, Talon will generate a unique code:
**Ghost Auth Code generated: 123456**

Send this code to your Telegram bot to bind your account:
`/start 123456`

## Maintenance and Monitoring

### Configuration Audit
Update your Telegram token or monitoring interval interactively:
```bash
talon config
```

### Service Filtering
Toggle monitoring for specific ports discovered during scans:
```bash
talon filter
```

### Start Monitoring
Run the background monitoring loop and Telegram bot:
```bash
talon monitor
```

## Dashboard Output
The tool periodically writes to `talon_dashboard.md`, which can be displayed in Homarr:
```markdown
# Talon Handler Dashboard
Last Updated: 2026-02-21 18:00:00

## Service Status
| Service | Port | Status |
| :--- | :--- | :--- |
| Jellyfin | 8096 | UP |
| Plex | 32400 | UP |
```

## Requirements
- Python 3.10+
- psutil
- python-telegram-bot
- typer
- rich

---
Created by abduznik
