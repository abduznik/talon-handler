import json
import os
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .constants import CONFIG_FILE

console = Console()

def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit OTP."""
    return "".join([str(secrets.randbelow(10)) for _ in range(6)])

class ConfigManager:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[red]Error loading config: {e}[/red]")
        return {}

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def interactive_audit(self):
        """Audits the configuration interactively."""
        updated_data = {}
        fields = [
            ("telegram_token", "Telegram Bot Token", ""),
            ("monitoring_interval", "Monitoring Interval (seconds)", 60),
        ]

        for key, label, default in fields:
            current_val = self.data.get(key)
            if current_val is not None:
                console.print(f"\n[cyan]Field [{label}] detected (Value: {current_val}).[/cyan]")
                action = Prompt.ask(
                    "Do you want to [K]eep, [R]ewrite, or [S]kip?",
                    choices=["K", "R", "S"],
                    default="K"
                ).upper()

                if action == "K":
                    updated_data[key] = current_val
                elif action == "R":
                    new_val = Prompt.ask(f"Enter new value for {label}")
                    updated_data[key] = new_val.strip("'\"")
                else:
                    continue
            else:
                new_val = Prompt.ask(f"Enter {label}", default=str(default))
                updated_data[key] = new_val.strip("'\"")

        # Always preserve or update core technical state
        updated_data["watchlist"] = self.data.get("watchlist", {})
        updated_data["chat_id"] = self.data.get("chat_id")
        
        self.data = updated_data
        self.save()

    def set_otp(self):
        otp = generate_otp()
        self.data["pending_otp"] = otp
        self.save()
        return otp

    def get_watchlist(self) -> Dict[str, bool]:
        return self.data.get("watchlist", {})

    def update_watchlist(self, watchlist: Dict[str, bool]):
        self.data["watchlist"] = watchlist
        self.save()
