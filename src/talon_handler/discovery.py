import psutil
import socket
from typing import Dict, List, Tuple
from .constants import COMMON_SERVICES

def scan_local_ports() -> List[Tuple[int, str]]:
    """
    Scans locally bound ports and maps them to real process names.
    Returns a list of (port, name).
    """
    found_ports = []
    
    try:
        # Get all connections with PID info
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                name = "Unknown"
                
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        name = proc.name()
                        # If it's a generic wrapper, try to show the command line or fallback
                        if name in ["docker-proxy", "python", "python3", "node"]:
                            # Try to see if we have a mapped name for better context
                            friendly = COMMON_SERVICES.get(port)
                            name = f"{name} ({friendly})" if friendly else name
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        name = COMMON_SERVICES.get(port, "System Process")
                
                found_ports.append((port, name))
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        # Fallback for restricted environments
        for port in COMMON_SERVICES.keys():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.01)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    found_ports.append((port, COMMON_SERVICES[port]))
                    
    # Remove duplicates and sort
    unique_found = {p: n for p, n in found_ports}
    return sorted(unique_found.items())

def check_service_health(port: int) -> bool:
    """Checks if a port is still listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0
