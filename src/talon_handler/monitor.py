import time
import psutil
import asyncio
from datetime import datetime
from typing import Dict
from .discovery import check_service_health
from .config import ConfigManager
from .constants import COMMON_SERVICES, DASHBOARD_FILE
from .telegram_bot import send_telegram_alert

class TalonMonitor:
    def __init__(self):
        self.config = ConfigManager()
        self.failure_counters: Dict[int, int] = {} # port -> consecutive failures

    def generate_dashboard(self, results: Dict[int, bool]):
        """Writes the Markdown dashboard."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        lines = [
            "# 🦅 Talon Handler Dashboard",
            f"**Last Updated:** `{timestamp}`",
            "",
            "## 🚀 System Vitals",
            f"- **CPU Usage:** `{cpu}%`",
            f"- **RAM Usage:** `{ram}%`",
            "",
            "## 📡 Service Status",
            "| Service | Port | Status |",
            "| :--- | :--- | :--- |"
        ]
        
        watchlist = self.config.get_watchlist()
        for port_str, enabled in watchlist.items():
            if not enabled: continue
            
            port = int(port_str)
            name = COMMON_SERVICES.get(port, "Unknown")
            status_icon = "✅ UP" if results.get(port) else "❌ DOWN"
            lines.append(f"| {name} | {port} | {status_icon} |")
            
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    async def run_loop(self):
        """Main monitoring loop."""
        token = self.config.data.get("telegram_token")
        chat_id = self.config.data.get("chat_id")
        interval = int(self.config.data.get("monitoring_interval", 60))

        while True:
            watchlist = self.config.get_watchlist()
            results = {}
            
            for port_str, enabled in watchlist.items():
                if not enabled: continue
                
                port = int(port_str)
                is_up = check_service_health(port)
                results[port] = is_up
                
                # Strike system
                if not is_up:
                    self.failure_counters[port] = self.failure_counters.get(port, 0) + 1
                    if self.failure_counters[port] == 3: # 3 strikes
                        if token and chat_id:
                            name = COMMON_SERVICES.get(port, "Unknown")
                            msg = f"⚠️ ALERT: Service '{name}' on port {port} is DOWN (3 consecutive failures)."
                            await send_telegram_alert(token, chat_id, msg)
                else:
                    # Reset counter if it recovers
                    if self.failure_counters.get(port, 0) >= 3:
                         if token and chat_id:
                            name = COMMON_SERVICES.get(port, "Unknown")
                            await send_telegram_alert(token, chat_id, f"✅ RECOVERED: Service '{name}' on port {port} is back UP.")
                    self.failure_counters[port] = 0
            
            self.generate_dashboard(results)
            await asyncio.sleep(interval)
