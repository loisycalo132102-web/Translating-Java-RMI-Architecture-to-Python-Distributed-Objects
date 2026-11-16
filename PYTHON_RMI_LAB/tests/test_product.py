"""Unit tests for Product model — equivalent to Product.java remote interface/data definition.

Maps Java RMI concepts:
  - Product.java (extends java.rmi.Remote)  → Product class
  - getName() / getDescription() / getPrice() → .name / .description / .price properties
  - Serializable fields → to_dict() / from_dict() for serpent wire format

Reference: server/Product.java and server/ProductImpl.java in JAVA_RMI_IV
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestProductConstruction:
    """Test Product instantiation with all required attributes."""

    def test_create_product_with_all_attributes(self):
        from product import Product

        p = Product(name="Laptop", description="Lenovo laptop", price=800000.0)
        assert p.name == "Laptop"
        assert p.description == "Lenovo laptop"
        assert p.price == 800000.0

    def test_create_product_with_zero_price(self):
        from product import Product

        p = Product(name="Free Item", description="Freebie", price=0.0)
        assert p.price == 0.0

    def test_create_product_matches_java_reference_data(self):
        """Verify we can create all 4 products from the Java Server.java."""
        from product import Product

        products = [
            Product(name="Laptop", description="Lenovo laptop", price=800000.0),
            Product(name="Mobile", description="MI 9 mobile", price=24000.0),
            Product(name="Bag", description="Branded bag", price=800.0),
            Product(name="Charger", description="MI Charger", price=230.0),
        ]
        assert len(products) == 4
        assert products[0].name == "Laptop"
        assert products[1].price == 24000.0
        assert products[2].description == "Branded bag"
        assert products[3].name == "Charger"

    def test_product_properties_are_read_only(self):
        from product import Product

        p = Product("Laptop", "Lenovo laptop", 800000.0)
        with pytest.raises(AttributeError):
            p.name = "Desktop"
        with pytest.raises(AttributeError):
            p.description = "New description"
        with pytest.raises(AttributeError):
            p.price = 1000.0
        with pytest.raises(AttributeError):
            p.quantity = 5


class TestProductSerialization:
    """Test dict serialization for Pyro5/serpent wire transfer."""

    def test_to_dict_returns_all_fields(self):
        from product import Product

        p = Product(name="Mobile", description="MI 9 mobile", price=24000.0)
        d = p.to_dict()
        assert d == {
            "name": "Mobile",
            "description": "MI 9 mobile",
            "price": 24000.0,
        }

    def test_from_dict_reconstructs_product(self):
        from product import Product

        data = {
            "name": "Bag",
            "description": "Branded bag",
            "price": 800.0,
        }
        p = Product.from_dict(data)
        assert p.name == "Bag"
        assert p.description == "Branded bag"
        assert p.price == 800.0

    def test_roundtrip_serialization(self):
        from product import Product

        original = Product(
            name="Charger", description="MI Charger", price=230.0
        )
        restored = Product.from_dict(original.to_dict())
        assert restored.to_dict() == original.to_dict()
        assert restored == original


class TestProductEquality:
    """Test value equality and hashing for Product instances."""

    def test_identical_products_are_equal(self):
        from product import Product

        p1 = Product("Laptop", "Lenovo laptop", 800000.0)
        p2 = Product("Laptop", "Lenovo laptop", 800000.0)
        assert p1 == p2
        assert hash(p1) == hash(p2)

    def test_different_products_are_not_equal(self):
        from product import Product

        base = Product("Laptop", "Lenovo laptop", 800000.0)
        different_name = Product("Desktop", "Lenovo laptop", 800000.0)
        different_desc = Product("Laptop", "Other laptop", 800000.0)
        different_price = Product("Laptop", "Lenovo laptop", 900000.0)

        assert base != different_name
        assert base != different_desc
        assert base != different_price

    def test_equality_with_non_product_returns_false(self):
        from product import Product

        p = Product("Laptop", "Lenovo laptop", 800000.0)
        assert p != "Laptop"
        assert p != 800000.0
        assert p != {"name": "Laptop", "description": "Lenovo laptop", "price": 800000.0}

    def test_product_usable_in_set_and_dict_keys(self):
        from product import Product

        p1 = Product("Laptop", "Lenovo laptop", 800000.0)
        p2 = Product("Laptop", "Lenovo laptop", 800000.0)
        product_set = {p1, p2}
        assert len(product_set) == 1


class TestProductRepr:
    """Test readable string representation."""

    def test_repr_contains_name_and_price(self):
        from product import Product

        p = Product(name="Laptop", description="Lenovo laptop", price=800000.0)
        r = repr(p)
        assert "Laptop" in r
        assert "800000.0" in r


class TestPyro5Compatibility:
    """Verify Product serialization is compatible with Pyro5 serpent wire format."""

    def test_product_dict_survives_serpent_roundtrip(self):
        """Ensure to_dict() output serializes and deserializes via serpent."""
        import serpent
        from product import Product

        original = Product(
            name="Laptop", description="Lenovo laptop", price=800000.0
        )
        serialized = serpent.dumps(original.to_dict())
        deserialized = serpent.loads(serialized)
        restored = Product.from_dict(deserialized)
        assert restored.to_dict() == original.to_dict()
        assert restored == original

