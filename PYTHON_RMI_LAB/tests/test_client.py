"""Unit and integration tests for PYTHON_RMI_LAB/client.py.

Equivalent to Client.java in Java RMI architecture.

Java RMI Mapping:
  - LocateRegistry.getRegistry("127.0.0.1", 9000)
      → Pyro5.api.Proxy(f"PYRO:{obj_id}@{host}:{port}")
  - (Product) registry.lookup("laptop")
      → proxy = get_product_proxy("laptop", host, port)
  - stub.getName(), stub.getDescription(), stub.getPrice()
      → proxy.getName(), proxy.getDescription(), proxy.getPrice()
  - RemoteException handling
      → Pyro5.errors.CommunicationError handling

Governed by:
  - testing-test-automation-engineer: Zero hard sleeps, deterministic server lifecycle fixtures
  - engineering-backend-architect: Graceful degradation and network error handling
  - engineering-code-reviewer: Clear assertions and contract validation
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from unittest.mock import patch

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import Pyro5.api
import Pyro5.errors

from product import Product
from server import create_catalog, create_server_daemon


@pytest.fixture
def running_server():
    """Starts a Pyro5 test daemon on localhost with an ephemeral port (port=0)."""
    catalog = create_catalog()
    daemon, uris = create_server_daemon(host="127.0.0.1", port=0, catalog=catalog)

    server_thread = threading.Thread(target=daemon.requestLoop, daemon=True)
    server_thread.start()

    host, port = daemon.locationStr.split(":")
    yield host, int(port), uris

    daemon.shutdown()
    server_thread.join(timeout=2.0)


class TestClientProxyResolution:
    """Test proxy acquisition and URI construction."""

    def test_get_product_proxy_returns_valid_proxy(self):
        from client import get_product_proxy

        proxy = get_product_proxy("laptop", host="127.0.0.1", port=9090)
        assert isinstance(proxy, Pyro5.api.Proxy)
        assert proxy._pyroUri.object == "laptop"
        assert proxy._pyroUri.host == "127.0.0.1"
        assert proxy._pyroUri.port == 9090
        proxy._pyroRelease()

    def test_get_product_proxy_custom_host_port(self):
        from client import get_product_proxy

        proxy = get_product_proxy("ram", host="192.168.1.50", port=8888)
        assert proxy._pyroUri.object == "ram"
        assert proxy._pyroUri.host == "192.168.1.50"
        assert proxy._pyroUri.port == 8888
        proxy._pyroRelease()


class TestClientRemoteInvocations:
    """Test remote method calls across process boundaries with running server."""

    def test_fetch_single_product_success(self, running_server):
        from client import fetch_product

        host, port, _ = running_server
        product = fetch_product("laptop", host=host, port=port)

        assert isinstance(product, Product)
        assert product.name == "Laptop"
        assert product.description == "Lenovo laptop"
        assert product.price == 800000.0

    def test_fetch_all_catalog_products(self, running_server):
        from client import fetch_all_products

        host, port, _ = running_server
        products = fetch_all_products(host=host, port=port)

        assert len(products) == 4
        assert set(products.keys()) == {"laptop", "ram", "bag", "charger"}

        assert products["laptop"].name == "Laptop"
        assert products["ram"].name == "Mobile"
        assert products["bag"].name == "Bag"
        assert products["charger"].name == "Charger"

    def test_fetch_product_handles_unreachable_server(self):
        """Client must catch CommunicationError gracefully and return None."""
        from client import fetch_product

        # Port 59999 is intentionally unused / closed
        result = fetch_product("laptop", host="127.0.0.1", port=59999)
        assert result is None


class TestClientRunExecution:
    """Test high-level client execution runner and CLI formatting."""

    def test_run_client_all_items(self, running_server, capsys):
        from client import run_client

        host, port, _ = running_server
        exit_code = run_client(host=host, port=port)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Connecting to Distributed RMI Server" in captured.out
        assert "Laptop" in captured.out
        assert "Lenovo laptop" in captured.out
        assert "Mobile" in captured.out
        assert "Bag" in captured.out
        assert "Charger" in captured.out

    def test_run_client_single_item(self, running_server, capsys):
        from client import run_client

        host, port, _ = running_server
        exit_code = run_client(host=host, port=port, item_key="bag")

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Bag" in captured.out
        assert "Branded bag" in captured.out

    def test_run_client_server_offline(self, capsys):
        from client import run_client

        # Port 59998 is offline
        exit_code = run_client(host="127.0.0.1", port=59998)
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "Could not connect" in captured.out


class TestClientCliParsing:
    """Test CLI arguments handling."""

    def test_cli_argument_parsing_defaults(self):
        from client import parse_cli_args

        with patch("sys.argv", ["client.py"]):
            args = parse_cli_args()
            assert args.host == "127.0.0.1"
            assert args.port == 9090
            assert args.item is None

    def test_cli_argument_parsing_custom(self):
        from client import parse_cli_args

        with patch("sys.argv", ["client.py", "--host", "10.0.0.1", "--port", "9000", "--item", "laptop"]):
            args = parse_cli_args()
            assert args.host == "10.0.0.1"
            assert args.port == 9000
            assert args.item == "laptop"
