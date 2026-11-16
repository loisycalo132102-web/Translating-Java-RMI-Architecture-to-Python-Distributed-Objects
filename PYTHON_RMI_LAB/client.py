"""Distributed Client and Remote Method Invocation.

Equivalent to Client.java in Java RMI architecture.

Java RMI Mapping:
  - LocateRegistry.getRegistry("127.0.0.1", 9000)
      → Connecting to Pyro5 daemon endpoint at host:port
  - (Product) registry.lookup("laptop")
      → proxy = get_product_proxy("laptop", host, port)
  - stub.getName(), stub.getDescription(), stub.getPrice()
      → proxy.getName(), proxy.getDescription(), proxy.getPrice()
  - RemoteException handling
      → Pyro5.errors.CommunicationError / PyroError handling

Reference: client/Client.java in JAVA_RMI_IV
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from product import Product
except ImportError:
    from PYTHON_RMI_LAB.product import Product

import Pyro5.api
import Pyro5.errors

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9090
DEFAULT_CATALOG_KEYS: List[str] = ["laptop", "ram", "bag", "charger"]


def get_product_proxy(
    obj_id: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> Pyro5.api.Proxy:
    """Create a Pyro5 client proxy targeting a remote object ID.

    Equivalent to `registry.lookup(obj_id)` in Java RMI.

    Args:
        obj_id: The registered object identifier (e.g. "laptop", "ram").
        host: Host address of the remote server daemon.
        port: Port number the server daemon is listening on.

    Returns:
        Pyro5.api.Proxy pointing to the remote product object.
    """
    uri = f"PYRO:{obj_id}@{host}:{port}"
    return Pyro5.api.Proxy(uri)


def fetch_product(
    obj_id: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> Optional[Product]:
    """Invoke remote methods on a product stub and reconstruct a local Product model.

    Equivalent to calling stub.getName(), stub.getDescription(), stub.getPrice()
    on the remote stub returned by the RMI registry in Client.java.

    Args:
        obj_id: The registered object identifier.
        host: Host address of the server daemon.
        port: Port number of the server daemon.

    Returns:
        Product instance if successfully queried, or None if remote call fails.
    """
    proxy = get_product_proxy(obj_id, host=host, port=port)
    try:
        # Remote method invocations across process boundary
        name = proxy.getName()
        description = proxy.getDescription()
        price = proxy.getPrice()
        return Product(name=name, description=description, price=price)
    except Pyro5.errors.CommunicationError as err:
        print(f"[Client Error] Failed to connect to remote object '{obj_id}' at {host}:{port}: {err}")
        return None
    except Pyro5.errors.PyroError as err:
        print(f"[Client Error] Remote invocation error for object '{obj_id}': {err}")
        return None
    finally:
        proxy._pyroRelease()


def fetch_all_products(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    catalog_keys: Optional[List[str]] = None,
) -> Dict[str, Product]:
    """Query and retrieve all registered product stubs from the remote server.

    Args:
        host: Host address of the server daemon.
        port: Port number of the server daemon.
        catalog_keys: List of object keys to query (defaults to standard assignment catalog).

    Returns:
        Dictionary mapping object ID to resolved Product instance.
    """
    if catalog_keys is None:
        catalog_keys = DEFAULT_CATALOG_KEYS

    results: Dict[str, Product] = {}
    for key in catalog_keys:
        product = fetch_product(key, host=host, port=port)
        if product is not None:
            results[key] = product

    return results


def run_client(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    item_key: Optional[str] = None,
) -> int:
    """Execute client lookup and display remote invocation results.

    Args:
        host: Server daemon host address.
        port: Server daemon port.
        item_key: Optional specific product key to query instead of all items.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    print("=" * 65)
    print(f"Connecting to Distributed RMI Server at {host}:{port}...")
    print("Equivalent to: LocateRegistry.getRegistry() & registry.lookup()")
    print("=" * 65)

    keys_to_query = [item_key] if item_key else DEFAULT_CATALOG_KEYS
    products = fetch_all_products(host=host, port=port, catalog_keys=keys_to_query)

    if not products:
        print(f"\n[Error] Could not connect or retrieve any products from server at {host}:{port}.")
        print("[Tip] Ensure the server is running: python PYTHON_RMI_LAB/server.py")
        return 1

    print(f"\nSuccessfully queried {len(products)} remote product object(s):\n")
    print(f"{'OBJECT ID':<12} | {'PRODUCT NAME':<18} | {'PRICE':<10} | {'DESCRIPTION'}")
    print("-" * 65)

    for obj_id, product in products.items():
        print(
            f"{obj_id.upper():<12} | {product.name:<18} | ${product.price:<9.2f} | {product.description}"
        )

    print("-" * 65)
    print("[Client] All remote method invocations completed successfully.\n")
    return 0


def parse_cli_args() -> argparse.Namespace:
    """Parse command line arguments for the client."""
    parser = argparse.ArgumentParser(
        description="Python Pyro5 Distributed RMI Client (Client.java equivalent)"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host address of server daemon (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port number of server daemon (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--item",
        choices=DEFAULT_CATALOG_KEYS,
        default=None,
        help="Query a specific product ID (e.g. laptop, ram, bag, charger)",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point for client execution."""
    args = parse_cli_args()
    exit_code = run_client(host=args.host, port=args.port, item_key=args.item)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
