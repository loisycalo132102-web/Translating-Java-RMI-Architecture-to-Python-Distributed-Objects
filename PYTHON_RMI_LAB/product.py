"""Product model and remote interface definition.

Equivalent to Product.java in the Java RMI architecture.

Java RMI Mapping:
  - Product.java (extends java.rmi.Remote)     → Product class
  - getName() throws RemoteException           → .name property
  - getDescription() throws RemoteException    → .description property
  - getPrice() throws RemoteException          → .price property
  - ProductImpl extends UnicastRemoteObject    → @Pyro5.api.expose in server.py
  - java.io.Serializable                       → to_dict() / from_dict()

This module defines the data model only. Remote exposure happens in server.py.
Reference: server/Product.java, server/ProductImpl.java in JAVA_RMI_IV
"""

from __future__ import annotations


class Product:
    """Product data model with Pyro5-compatible serialization.

    Mirrors the Java Product remote interface with three methods:
      - getName()        → .name property
      - getDescription() → .description property
      - getPrice()       → .price property
    """

    __slots__ = ("_name", "_description", "_price")

    def __init__(self, name: str, description: str, price: float) -> None:
        self._name = name
        self._description = description
        self._price = float(price)

    # --- Read-only properties (equivalent to Java getter methods) ---

    @property
    def name(self) -> str:
        """Equivalent to Product.getName() in Java RMI."""
        return self._name

    @property
    def description(self) -> str:
        """Equivalent to Product.getDescription() in Java RMI."""
        return self._description

    @property
    def price(self) -> float:
        """Equivalent to Product.getPrice() in Java RMI."""
        return self._price

    # --- Serialization for Pyro5/serpent wire transfer ---

    def to_dict(self) -> dict:
        """Serialize to dict for Pyro5 serpent transfer.

        Equivalent to Java Serializable interface — converts the object
        to a format that can cross process boundaries via Pyro5.
        """
        return {
            "name": self._name,
            "description": self._description,
            "price": self._price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        """Reconstruct Product from a dict received over the wire.

        Equivalent to deserializing a Java Serializable object on the
        client side after RMI transfer.
        """
        return cls(
            name=data["name"],
            description=data["description"],
            price=data["price"],
        )

    def __repr__(self) -> str:
        return (
            f"Product(name={self._name!r}, description={self._description!r}, "
            f"price={self._price})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return (
            self._name == other._name
            and self._description == other._description
            and self._price == other._price
        )

    def __hash__(self) -> int:
        return hash((self._name, self._description, self._price))
