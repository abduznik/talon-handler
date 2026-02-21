import typer
import asyncio
import os
import signal
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional
from .config import ConfigManager
from .discovery import scan_local_ports
from .monitor import TalonMonitor
from .telegram_bot import TalonBot
from .constants import PID_FILE

app = typer.Typer(help="🦅 Talon Handler: Homelab Service Discovery & Monitoring")
console = Console()

def is_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return pid
        except (ProcessLookupError, ValueError, OverflowError, PermissionError):
            if os.path.exists(PID_FILE): os.remove(PID_FILE)
    return None

@app.command()
def headstart():
    """Initial setup and first-time scan."""
    config = ConfigManager()
    if config.data and "telegram_token" in config.data:
        overwrite = typer.confirm("Configuration already exists. Reset everything?")
        if not overwrite:
            raise typer.Exit()

    console.print("[bold green]🚀 Talon Headstart Initializing...[/bold green]")
    
    # 1. Smart Scan
    with console.status("[cyan]Performing Smart Scan of local ports...[/cyan]"):
        found = scan_local_ports()
    
    table = Table(title="Discovered Services")
    table.add_column("Port", style="cyan")
    table.add_column("Detected Process / Service", style="magenta")
    
    watchlist = {}
    service_names = {}
    for port, name in found:
        table.add_row(str(port), name)
        watchlist[str(port)] = True 
        service_names[str(port)] = name
    
    console.print(table)
    config.data["watchlist"] = watchlist
    config.data["service_names"] = service_names
    
    # 2. Config Audit
    config.interactive_audit()
    
    # 3. Trigger OTP
    otp = config.set_otp()
    console.print(f"\n[bold yellow]👻 Ghost Auth Code generated: {otp}[/bold yellow]")
    console.print(f"Send this code to your bot using: /start {otp}")

@app.command()
def config():
    """Interactive maintenance hub for configuration."""
    cfg = ConfigManager()
    cfg.interactive_audit()
    console.print("[green]Configuration updated successfully.[/green]")

@app.command()
def telegram(new: bool = typer.Option(False, "--new", help="Generate a fresh OTP")):
    """Telegram management and Ghost Auth."""
    cfg = ConfigManager()
    if new:
        otp = cfg.set_otp()
        console.print(f"[bold yellow]New Ghost Auth Code: {otp}[/bold yellow]")
        console.print("Previous pending codes have been invalidated.")
    else:
        chat_id = cfg.data.get("chat_id")
        if chat_id:
            console.print(f"[green]Telegram is bound to Chat ID: {chat_id}[/green]")
        else:
            otp = cfg.data.get("pending_otp", "None")
            console.print(f"[yellow]Status: Pending Ghost Auth. Active Code: {otp}[/yellow]")

@app.command()
def filter():
    """Interactive toggle for monitored services."""
    cfg = ConfigManager()
    watchlist = cfg.get_watchlist()
    
    if not watchlist:
        console.print("[red]No services in watchlist. Run 'talon headstart' first.[/red]")
        return

    console.print("[bold cyan]Monitoring Filter (Toggle Status)[/bold cyan]")
    
    updated_watchlist = {}
    for port_str, status in watchlist.items():
        state = "ENABLED" if status else "DISABLED"
        toggle = typer.confirm(f"Port {port_str} ({state}) - Keep enabled?")
        updated_watchlist[port_str] = toggle
        
    cfg.update_watchlist(updated_watchlist)
    console.print("[green]Watchlist filters updated.[/green]")

@app.command()
def monitor(detach: bool = typer.Option(False, "--detach", "-d", help="Run in the background")):
    """Starts the background monitoring loop and Telegram bot."""
    if is_running():
        console.print("[yellow]Talon is already running.[/yellow]")
        return

    if detach:
        # Launch same command without --detach in background
        cmd = [sys.executable, "-m", "talon_handler.main", "monitor"]
        # Use subprocess to detach
        if os.name == 'nt':
            # Windows background
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        else:
            # Linux background
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
        
        console.print("[bold green]🦅 Talon Eye has taken flight in the background.[/bold green]")
        return

    # Write PID file
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    cfg = ConfigManager()
    token = cfg.data.get("telegram_token")
    
    if not token:
        console.print("[red]Telegram Token not found. Run 'talon headstart' first.[/red]")
        if os.path.exists(PID_FILE): os.remove(PID_FILE)
        return

    console.print("[bold green]🦅 Talon Eye is watching...[/bold green]")
    
    async def start_services():
        bot = TalonBot(token)
        monitor = TalonMonitor()
        await asyncio.gather(bot.run(), monitor.run_loop())

    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        console.print("\n[yellow]Talon Eye closed.[/yellow]")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

@app.command()
def stop():
    """Stops the background Talon monitor."""
    pid = is_running()
    if pid:
        console.print(f"[cyan]Stopping Talon (PID: {pid})...[/cyan]")
        try:
            os.kill(pid, signal.SIGTERM)
            # Short wait for cleanup
            import time
            time.sleep(0.5)
            if os.path.exists(PID_FILE): os.remove(PID_FILE)
            console.print("[green]Talon stopped successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to stop Talon: {e}[/red]")
    else:
        console.print("[yellow]Talon is not currently running.[/yellow]")

if __name__ == "__main__":
    app()
