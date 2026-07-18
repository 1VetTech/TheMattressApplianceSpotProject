"""Tests for public inventory validation."""

from decimal import Decimal

import pytest

from inventory_automation.validation import validate_inventory_rows


def make_valid_row() -> dict[str, str]:
    """Return one valid public inventory row."""
    return {
        "SKU": " bed001 ",
        "Category": " Bedroom ",
        "Item": " Cayboni   Bedroom Set ",
        "Sell Price": "$999",
        "Qty": "1",
        "Description": " Whitewash bedroom set. ",
        "Image URL": "https://example.com/BED001.jpg",
        "Color": "Whitewash",
        "Website Status": "Published",
    }


def test_valid_row_is_normalized() -> None:
    """A valid public row should become a Product."""
    products, warnings = validate_inventory_rows([make_valid_row()])

    assert warnings == []
    assert len(products) == 1

    product = products[0]

    assert product.sku == "BED001"
    assert product.category == "Bedroom"
    assert product.item == "Cayboni Bedroom Set"
    assert product.sell_price == Decimal("999")
    assert product.quantity == 1
    assert product.website_status == "Published"


def test_duplicate_sku_raises_error() -> None:
    """Duplicate SKUs should stop validation."""
    first_row = make_valid_row()
    second_row = make_valid_row()
    second_row["Item"] = "Another Product"

    with pytest.raises(ValueError, match="Duplicate SKU"):
        validate_inventory_rows([first_row, second_row])


def test_missing_sell_price_raises_error() -> None:
    """Published products must have a valid selling price."""
    row = make_valid_row()
    row["Sell Price"] = ""

    with pytest.raises(ValueError, match="valid Sell Price"):
        validate_inventory_rows([row])


def test_nonpublished_row_is_skipped() -> None:
    """Rows that are not Published should not reach the website."""
    row = make_valid_row()
    row["Website Status"] = "Draft"

    products, warnings = validate_inventory_rows([row])

    assert products == []
    assert any("was skipped" in warning for warning in warnings)
