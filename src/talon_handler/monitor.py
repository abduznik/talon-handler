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
        self.alert_sent: Dict[int, bool] = {} # port -> alert sent status

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
        service_names = self.config.data.get("service_names", {})
        for port_str, enabled in watchlist.items():
            if not enabled: continue
            
            port = int(port_str)
            name = service_names.get(port_str, COMMON_SERVICES.get(port, "Unknown"))
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
            try:
                self.config.reload() # Pick up new watchlist or token changes
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
                        strikes = self.failure_counters[port]
                        
                        # Alert if 3+ strikes and we haven't successfully notified yet
                        if strikes >= 3 and not self.alert_sent.get(port, False):
                            if token and chat_id:
                                name = self.config.data.get("service_names", {}).get(port_str, "Unknown")
                                msg = f"⚠️ ALERT: Service '{name}' on port {port} is DOWN (Strikes: {strikes})."
                                try:
                                    await send_telegram_alert(token, int(chat_id), msg)
                                    self.alert_sent[port] = True
                                    with open("talon.log", "a") as log:
                                        log.write(f"{datetime.now()}: [ALERT SENT] Port {port}\n")
                                except Exception as te:
                                    with open("talon.log", "a") as log:
                                        log.write(f"{datetime.now()}: [ALERT FAILED] Port {port}: {te}\n")
                    else:
                        # Reset counter and check for recovery
                        if self.failure_counters.get(port, 0) >= 3:
                             if token and chat_id:
                                name = self.config.data.get("service_names", {}).get(port_str, "Unknown")
                                try:
                                    await send_telegram_alert(token, int(chat_id), f"✅ RECOVERED: Service '{name}' on port {port} is back UP.")
                                except Exception:
                                    pass
                        self.failure_counters[port] = 0
                        self.alert_sent[port] = False
                
                self.generate_dashboard(results)
                
                # HEARTBEAT
                with open("talon.log", "a") as log:
                    log.write(f"{datetime.now()}: Heartbeat - Scan completed ({len(results)} ports checked).\n")
            
            except Exception as e:
                with open("talon.log", "a") as log:
                    log.write(f"{datetime.now()}: Loop Error: {e}\n")
            
            await asyncio.sleep(interval)
