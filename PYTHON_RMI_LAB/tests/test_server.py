"""Unit and integration tests for PYTHON_RMI_LAB/server.py.

Maps Java RMI concepts:
  - ProductImpl.java                → ProductImpl class exposed via @Pyro5.api.expose
  - Server.java (object export)     → daemon.register(obj, objectId=...)
  - LocateRegistry.getRegistry()    → Pyro5.api.Proxy connection
  - registry.bind("laptop", stub)   → Pyro5 objectId binding

Governed by testing-test-automation-engineer:
  - Deterministic thread lifecycle (no hard sleeps)
  - Clear assertion failure messages
  - Isolation of network sockets via dynamic/test ports
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

# Add project root to sys.path for direct imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import Pyro5.api


class TestProductImpl:
    """Test the remote ProductImpl object before network exposure."""

    def test_product_impl_initialization(self):
        from server import ProductImpl

        p = ProductImpl("Laptop", "Lenovo laptop", 800000.0)
        assert p.name == "Laptop"
        assert p.description == "Lenovo laptop"
        assert p.price == 800000.0

    def test_product_impl_java_rmi_getters(self):
        """Java RMI requires getName(), getDescription(), and getPrice()."""
        from server import ProductImpl

        p = ProductImpl("Mobile", "MI 9 mobile", 24000.0)
        assert p.getName() == "Mobile"
        assert p.getDescription() == "MI 9 mobile"
        assert p.getPrice() == 24000.0

    def test_product_impl_is_exposed_for_pyro(self):
        """Verify the class or methods have @Pyro5.api.expose applied."""
        from server import ProductImpl

        # Pyro5 sets _pyroExposed attribute on exposed classes/methods
        assert getattr(ProductImpl, "_pyroExposed", False) is True

    def test_product_impl_repr(self):
        from server import ProductImpl

        p = ProductImpl("Bag", "Branded bag", 800.0)
        assert "ProductImpl" in repr(p)
        assert "Bag" in repr(p)

    def test_product_impl_to_dict(self):
        from server import ProductImpl

        p = ProductImpl("Charger", "MI Charger", 230.0)
        data = p.to_dict()
        assert data == {
            "name": "Charger",
            "description": "MI Charger",
            "price": 230.0,
        }


class TestCatalogCreation:
    """Test standard inventory catalog generation matching Server.java."""

    def test_create_catalog_contains_reference_items(self):
        from server import create_catalog

        catalog = create_catalog()
        assert set(catalog.keys()) == {"laptop", "ram", "bag", "charger"}

        # Verify items correspond to Java RMI Server.java definitions
        assert catalog["laptop"].getName() == "Laptop"
        assert catalog["laptop"].getDescription() == "Lenovo laptop"
        assert catalog["laptop"].getPrice() == 800000.0

        assert catalog["ram"].getName() == "Mobile"
        assert catalog["ram"].getDescription() == "MI 9 mobile"
        assert catalog["ram"].getPrice() == 24000.0

        assert catalog["bag"].getName() == "Bag"
        assert catalog["bag"].getDescription() == "Branded bag"
        assert catalog["bag"].getPrice() == 800.0

        assert catalog["charger"].getName() == "Charger"
        assert catalog["charger"].getDescription() == "MI Charger"
        assert catalog["charger"].getPrice() == 230.0


class TestServerDaemonLifecycle:
    """Test Pyro5 Daemon creation, object registration, and remote calls."""

    @pytest.fixture
    def running_server(self):
        """Starts a test Pyro5 daemon on localhost with an ephemeral port."""
        from server import create_catalog, create_server_daemon

        catalog = create_catalog()
        # port=0 binds to an available ephemeral OS port to avoid collisions
        daemon, uris = create_server_daemon(host="127.0.0.1", port=0, catalog=catalog)

        server_thread = threading.Thread(target=daemon.requestLoop, daemon=True)
        server_thread.start()

        yield daemon, uris

        daemon.shutdown()
        server_thread.join(timeout=2.0)

    def test_remote_product_method_invocation(self, running_server):
        """Test that a client proxy can remotely invoke getName, getDescription, getPrice."""
        daemon, uris = running_server
        laptop_uri = uris["laptop"]

        # Client proxy connecting directly to remote object
        with Pyro5.api.Proxy(laptop_uri) as proxy:
            assert proxy.getName() == "Laptop"
            assert proxy.getDescription() == "Lenovo laptop"
            assert proxy.getPrice() == 800000.0

    def test_all_catalog_proxies_accessible(self, running_server):
        """Verify each registered catalog product is reachable and returns valid data."""
        daemon, uris = running_server

        expected = {
            "laptop": ("Laptop", "Lenovo laptop", 800000.0),
            "ram": ("Mobile", "MI 9 mobile", 24000.0),
            "bag": ("Bag", "Branded bag", 800.0),
            "charger": ("Charger", "MI Charger", 230.0),
        }

        for obj_id, (name, desc, price) in expected.items():
            uri = uris[obj_id]
            with Pyro5.api.Proxy(uri) as proxy:
                assert proxy.getName() == name
                assert proxy.getDescription() == desc
                assert proxy.getPrice() == price
