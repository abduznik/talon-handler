import typer
import asyncio
from rich.console import Console
from rich.table import Table
from typing import Optional
from .config import ConfigManager
from .discovery import scan_local_ports
from .monitor import TalonMonitor
from .telegram_bot import TalonBot

app = typer.Typer(help="🦅 Talon Handler: Homelab Service Discovery & Monitoring")
console = Console()

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
    table.add_column("Mapped Service", style="magenta")
    
    watchlist = {}
    for port, name in found:
        table.add_row(str(port), name)
        watchlist[str(port)] = True # Enable all by default on first scan
    
    console.print(table)
    config.data["watchlist"] = watchlist
    
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
def monitor():
    """Starts the background monitoring loop and Telegram bot."""
    cfg = ConfigManager()
    token = cfg.data.get("telegram_token")
    
    if not token:
        console.print("[red]Telegram Token not found. Run 'talon headstart' first.[/red]")
        return

    console.print("[bold green]🦅 Talon Eye is watching...[/bold green]")
    
    async def start_services():
        bot = TalonBot(token)
        monitor = TalonMonitor()
        
        # Run bot and monitor loop concurrently
        await asyncio.gather(
            bot.run(),
            monitor.run_loop()
        )

    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        console.print("\n[yellow]Talon Eye closed.[/yellow]")

if __name__ == "__main__":
    app()
