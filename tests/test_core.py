import pytest
from talon_handler.config import generate_otp
from talon_handler.discovery import scan_local_ports

def test_otp_generation():
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()

def test_discovery_structure():
    # Even if no ports are listening, the return should be a list
    found = scan_local_ports()
    assert isinstance(found, list)
    for port, name in found:
        assert isinstance(port, int)
        assert isinstance(name, str)
