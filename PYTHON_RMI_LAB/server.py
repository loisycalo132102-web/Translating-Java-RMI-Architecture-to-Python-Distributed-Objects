"""Distributed Server and Remote Object Implementation.

Equivalent to Server.java, ProductImpl.java, and ServerImpl.java in Java RMI.

Java RMI Mapping:
  - ProductImpl.java (implements Product, extends UnicastRemoteObject)
      → ProductImpl class exposed via @Pyro5.api.expose
  - Server.java (UnicastRemoteObject.exportObject)
      → daemon.register(product, objectId=...)
  - LocateRegistry.getRegistry("127.0.0.1", 9000) & registry.bind(...)
      → Pyro5.api.Daemon(host="127.0.0.1", port=9090) binding objectId

Reference: server/ProductImpl.java, server/Server.java in JAVA_RMI_IV
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple

try:
    from product import Product
except ImportError:
    from PYTHON_RMI_LAB.product import Product

import Pyro5.api


@Pyro5.api.expose
class ProductImpl:
    """Remote product object implementation.

    Mirrors ProductImpl.java which implements the remote Product interface.
    Each method can be invoked across process boundaries by a Pyro5 client proxy.
    """

    def __init__(self, name: str, description: str, price: float) -> None:
        self._product = Product(name=name, description=description, price=price)

    # --- Java RMI interface methods ---

    def getName(self) -> str:
        """Equivalent to Product.getName() in Java RMI."""
        print(f"[Server] Invoked getName() -> {self._product.name}")
        return self._product.name

    def getDescription(self) -> str:
        """Equivalent to Product.getDescription() in Java RMI."""
        print(f"[Server] Invoked getDescription() -> {self._product.description}")
        return self._product.description

    def getPrice(self) -> float:
        """Equivalent to Product.getPrice() in Java RMI."""
        print(f"[Server] Invoked getPrice() -> {self._product.price}")
        return self._product.price

    # --- Idiomatic Python properties ---

    @property
    def name(self) -> str:
        return self._product.name

    @property
    def description(self) -> str:
        return self._product.description

    @property
    def price(self) -> float:
        return self._product.price

    # --- Wire serialization helper ---

    def to_dict(self) -> dict:
        """Serialize inner Product to dict for serialization."""
        return self._product.to_dict()

    def __repr__(self) -> str:
        return f"ProductImpl(name={self._product.name!r}, price={self._product.price})"


def create_catalog() -> Dict[str, ProductImpl]:
    """Create the reference product inventory matching Server.java in JAVA_RMI_IV.

    Original Java mapping:
      ProductImpl p1 = new ProductImpl("Laptop", "Lenovo laptop", 800000.0);
      ProductImpl p2 = new ProductImpl("Mobile", "MI 9 mobile", 24000.0);
      ProductImpl p3 = new ProductImpl("Bag", "Branded bag", 800.0);
      ProductImpl p4 = new ProductImpl("Charger", "MI Charger", 230.0);
      registry.bind("laptop", stub1);
      registry.bind("ram", stub2);
      registry.bind("bag", stub3);
      registry.bind("charger", stub4);
    """
    return {
        "laptop": ProductImpl("Laptop", "Lenovo laptop", 800000.0),
        "ram": ProductImpl("Mobile", "MI 9 mobile", 24000.0),
        "bag": ProductImpl("Bag", "Branded bag", 800.0),
        "charger": ProductImpl("Charger", "MI Charger", 230.0),
    }


def create_server_daemon(
    host: str = "127.0.0.1",
    port: int = 9090,
    catalog: Dict[str, ProductImpl] | None = None,
) -> Tuple[Pyro5.api.Daemon, Dict[str, str]]:
    """Initialize Pyro5 daemon and register catalog remote objects.

    Equivalent to LocateRegistry.getRegistry() and registry.bind() in Java RMI.

    Args:
        host: Host IP to listen on.
        port: Port number (0 for dynamic/ephemeral port in tests).
        catalog: Mapping of objectId to ProductImpl instance.

    Returns:
        Tuple of (daemon instance, dict mapping objectId to Pyro URI string).
    """
    if catalog is None:
        catalog = create_catalog()

    daemon = Pyro5.api.Daemon(host=host, port=port)
    uris: Dict[str, str] = {}

    for obj_id, product_impl in catalog.items():
        uri = daemon.register(product_impl, objectId=obj_id)
        uris[obj_id] = str(uri)

    return daemon, uris


def start_server(host: str = "127.0.0.1", port: int = 9090) -> None:
    """Start the Pyro5 server daemon and enter the request loop."""
    print("=" * 60)
    print("Server is booting....")
    print(f"Target host: {host}:{port}")
    print("=" * 60)

    catalog = create_catalog()
    daemon, uris = create_server_daemon(host=host, port=port, catalog=catalog)

    print("\nRegistered Remote Objects (Java RMI equivalent):")
    for obj_id, uri in uris.items():
        print(f"  • {obj_id.upper():<8} -> {uri}")

    print("\n[Server] Ready to accept remote method invocations.")
    print("[Server] Press Ctrl+C to stop server.\n" + "-" * 60)

    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("\n[Server] Shutdown signal received. Closing daemon...")
    finally:
        daemon.shutdown()
        print("[Server] Server stopped successfully.")


def main() -> None:
    """CLI entry point for launching the server daemon."""
    parser = argparse.ArgumentParser(
        description="Python Pyro5 Distributed RMI Server"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind server daemon (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Port to bind server daemon (default: 9090)",
    )
    args = parser.parse_args()

    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
