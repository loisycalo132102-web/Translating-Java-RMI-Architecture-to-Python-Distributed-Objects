"""Cross-process end-to-end integration tests for PYTHON_RMI_LAB.

Validates the full distributed system across real process boundaries:
  - Spawns `server.py` as an independent subprocess.
  - Verifies socket readiness deterministically without hard sleeps.
  - Spawns `client.py` as an independent subprocess.
  - Verifies return codes, stdout output, catalog queries, and error handling.

Governed by:
  - testing-test-automation-engineer: Zero hard sleeps, deterministic socket polling,
    isolated ephemeral ports, robust subprocess teardown.
  - engineering-backend-architect: True multi-process distributed RPC verification.
  - engineering-code-reviewer: Clear assertions and fail-safe process cleanup.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator, Tuple

import pytest

# Ensure project root is known
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_SCRIPT = str(PROJECT_ROOT / "server.py")
CLIENT_SCRIPT = str(PROJECT_ROOT / "client.py")


def find_free_port() -> int:
    """Find and return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_port(host: str, port: int, timeout: float = 5.0) -> bool:
    """Deterministically poll until the socket port is accepting TCP connections.

    Condition-based wait (zero arbitrary hard sleeps), compliant with
    testing-test-automation-engineer determinism standards.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.05)
    return False


@pytest.fixture(scope="function")
def live_server_process() -> Generator[Tuple[str, int, subprocess.Popen], None, None]:
    """Launch the Pyro5 server in a real independent subprocess and guarantee clean shutdown."""
    host = "127.0.0.1"
    port = find_free_port()

    proc = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, "--host", host, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    ready = wait_for_port(host, port, timeout=5.0)
    assert ready, f"Server process on {host}:{port} failed to start within timeout"

    try:
        yield host, port, proc
    finally:
        # Graceful termination first
        proc.terminate()
        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2.0)


def test_e2e_client_queries_all_catalog_items(
    live_server_process: Tuple[str, int, subprocess.Popen]
) -> None:
    """Verifies that running client.py queries all products and formats stdout correctly."""
    host, port, _ = live_server_process

    result = subprocess.run(
        [sys.executable, CLIENT_SCRIPT, "--host", host, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10.0,
    )

    assert result.returncode == 0
    stdout = result.stdout

    # Verify connection banner
    assert f"Connecting to Distributed RMI Server at {host}:{port}" in stdout

    # Verify all four products from the assignment specification appear in output
    assert "LAPTOP" in stdout
    assert "RAM" in stdout
    assert "BAG" in stdout
    assert "CHARGER" in stdout

    # Verify prices and descriptions matching reference Java RMI catalog
    assert "$800000.00" in stdout
    assert "$24000.00" in stdout
    assert "$800.00" in stdout
    assert "$230.00" in stdout
    assert "Lenovo laptop" in stdout
    assert "MI 9 mobile" in stdout
    assert "Branded bag" in stdout
    assert "MI Charger" in stdout

    # Verify completion message
    assert "All remote method invocations completed successfully." in stdout


def test_e2e_client_queries_specific_item(
    live_server_process: Tuple[str, int, subprocess.Popen]
) -> None:
    """Verifies that running client.py with --item queries only the designated item."""
    host, port, _ = live_server_process

    result = subprocess.run(
        [sys.executable, CLIENT_SCRIPT, "--host", host, "--port", str(port), "--item", "ram"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10.0,
    )

    assert result.returncode == 0
    stdout = result.stdout

    assert "RAM" in stdout
    assert "$24000.00" in stdout
    assert "MI 9 mobile" in stdout

    # Other items should not be queried
    assert "LAPTOP" not in stdout
    assert "CHARGER" not in stdout


def test_e2e_client_handles_unreachable_server_gracefully() -> None:
    """Verifies that client.py exits with error code 1 and helpful diagnostics when server is offline."""
    host = "127.0.0.1"
    unused_port = find_free_port()

    result = subprocess.run(
        [sys.executable, CLIENT_SCRIPT, "--host", host, "--port", str(unused_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10.0,
    )

    assert result.returncode == 1
    stdout = result.stdout

    assert "[Client Error] Failed to connect to remote object" in stdout
    assert "Could not connect or retrieve any products from server" in stdout
    assert "[Tip] Ensure the server is running" in stdout
