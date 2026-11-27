
"""Tests for public inventory JSON export."""

import json

from inventory_automation.exporter import write_inventory_json
from inventory_automation.models import Product


def make_product() -> Product:
    """Create a sample product for exporter tests."""
    return Product(
        sku="BED001",
        category="Bedroom",
        item="Cayboni Bedroom Set",
        quantity=1,
        description="Whitewash bedroom set.",
        image_url="https://example.com/bedroom.jpg",
        product_url="https://www.ashleyfurniture.com/product.html",
        color="Whitewash",
        website_status="Published",
    )


def test_export_creates_inventory_json(tmp_path) -> None:
    """Export should create the requested JSON file."""
    output_path = tmp_path / "inventory.json"

    write_inventory_json([make_product()], output_path)

    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert data["product_count"] == 1
    assert len(data["products"]) == 1


def test_export_contains_only_public_fields(tmp_path) -> None:
    """Private pricing and Ashley product links must not be exported."""
    output_path = tmp_path / "inventory.json"

    write_inventory_json([make_product()], output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    product = data["products"][0]

    assert product["sku"] == "BED001"
    assert product["item"] == "Cayboni Bedroom Set"
    assert product["image_url"] == "https://example.com/bedroom.jpg"

    assert "sell_price" not in product
    assert "display_price" not in product
    assert "price" not in product
    assert "apk" not in product
    assert "product_url" not in product

    assert "ashleyfurniture.com" not in json.dumps(product)


def test_export_replaces_existing_inventory(tmp_path) -> None:
    """A successful export should replace the previous JSON file."""
    output_path = tmp_path / "inventory.json"
    output_path.write_text('{"old": true}', encoding="utf-8")

    write_inventory_json([make_product()], output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert data["product_count"] == 1
    assert "old" not in data
    assert not output_path.with_suffix(".tmp").exists()


def test_empty_inventory_exports_zero_products(tmp_path) -> None:
    """An empty inventory should produce valid JSON with zero products."""
    output_path = tmp_path / "inventory.json"

    write_inventory_json([], output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert data["product_count"] == 0
    assert data["products"] == []
