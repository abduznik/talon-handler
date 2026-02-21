import pytest
from talon_handler.config import generate_otp
from talon_handler.discovery import scan_local_ports
from talon_handler.main import app
from typer.testing import CliRunner
from talon_handler import __version__

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

def test_version_flag():
    """Test that --version flag displays the correct version."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"Talon Handler version: {__version__}" in result.output
