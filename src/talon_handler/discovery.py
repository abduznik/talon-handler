import psutil
import socket
from typing import Dict, List, Tuple
from .constants import COMMON_SERVICES

def scan_local_ports() -> List[Tuple[int, str]]:
    """
    Scans locally bound ports and maps them to service names.
    Returns a list of (port, service_name).
    """
    found_ports = []
    
    # Use psutil to find all listening connections
    try:
        connections = psutil.net_connections(kind='inet')
        listening = [conn for conn in connections if conn.status == 'LISTEN']
        
        unique_ports = set()
        for conn in listening:
            port = conn.laddr.port
            if port not in unique_ports:
                unique_ports.add(port)
                service_name = COMMON_SERVICES.get(port, "Unknown Service")
                found_ports.append((port, service_name))
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        # Fallback to a basic socket scan for common ports if psutil fails (e.g. permissions)
        for port in COMMON_SERVICES.keys():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.01)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    found_ports.append((port, COMMON_SERVICES[port]))
                    
    return sorted(found_ports)

def check_service_health(port: int) -> bool:
    """Checks if a port is still listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0
