
"""Tests for public inventory validation."""

import pytest

from inventory_automation.validation import (
    REQUIRED_COLUMNS,
    validate_inventory_rows,
)


def make_valid_row() -> dict[str, str]:
    """Return one valid public inventory row."""
    return {
        "SKU": " bed001 ",
        "Category": " Bedroom ",
        "Item": " Cayboni   Bedroom Set ",
        "Qty": "1",
        "WEBSITE LINK": (
            "https://www.ashleyfurniture.com/"
            "p/bladen_3-piece_sectional/APK-12021-3R.html"
        ),
        "imageLinks": (
            "https://cdn.ashley.com/assets/12021-55-46-67-10X8-CROP.jpg"
            "?width=1920&height=1920&fit=bounds&quality=90&format=auto"
        ),
        "APK": "APK-12021-3R",
        "Sell Price": "Call store for pricing",
        "Description": " Whitewash bedroom set. ",
        "Color": "Whitewash",
        "Website Status": "Published",
    }


def test_valid_row_is_normalized() -> None:
    """A valid public row should become a normalized Product."""
    products, warnings = validate_inventory_rows([make_valid_row()])

    assert not warnings
    assert len(products) == 1

    product = products[0]

    assert product.sku == "BED001"
    assert product.category == "Bedroom"
    assert product.item == "Cayboni Bedroom Set"
    assert product.quantity == 1
    assert product.website_status == "Published"
    assert product.color == "Whitewash"


def test_website_link_is_optional() -> None:
    """A blank WEBSITE LINK should not prevent product publishing."""
    row = make_valid_row()
    row["WEBSITE LINK"] = ""

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1
    assert products[0].product_url == ""
    assert not warnings


def test_website_link_column_is_not_required() -> None:
    """The inventory can validate even without the WEBSITE LINK column."""
    row = make_valid_row()
    row.pop("WEBSITE LINK")

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1
    assert products[0].product_url == ""
    assert not warnings


def test_invalid_website_link_does_not_skip_product() -> None:
    """An invalid optional product link should create a warning only."""
    row = make_valid_row()
    row["WEBSITE LINK"] = "not-a-valid-url"

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1
    assert products[0].product_url == ""
    assert any("invalid WEBSITE LINK URL" in warning for warning in warnings)


def test_duplicate_sku_raises_error() -> None:
    """Duplicate SKUs should stop validation."""
    first_row = make_valid_row()
    second_row = make_valid_row()
    second_row["Item"] = "Another Product"

    with pytest.raises(ValueError, match="Duplicate SKU"):
        validate_inventory_rows([first_row, second_row])


def test_nonpublished_row_is_skipped() -> None:
    """Rows that are not Published should not reach the website."""
    row = make_valid_row()
    row["Website Status"] = "Draft"

    products, warnings = validate_inventory_rows([row])

    assert not products
    assert any("was skipped" in warning for warning in warnings)


def test_product_and_image_urls_are_read_correctly() -> None:
    """The Ashley link and image URL should be read from their columns."""
    row = make_valid_row()

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1

    product = products[0]

    assert product.image_url.startswith("https://cdn.ashley.com/")
    assert product.product_url.startswith(
        "https://www.ashleyfurniture.com/"
    )
    assert not warnings


def test_apk_is_not_used_as_product_url() -> None:
    """APK is an internal model identifier, not a product URL."""
    row = make_valid_row()
    row["APK"] = "APK-12021-3R"

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1
    assert product_url_is_not_apk(products[0].product_url)
    assert not warnings


def product_url_is_not_apk(product_url: str) -> bool:
    """Return True when the product URL is not an APK identifier."""
    return product_url != "APK-12021-3R"


def test_sell_price_is_ignored() -> None:
    """The Sell Price column should not affect inventory validation."""
    row = make_valid_row()
    row["Sell Price"] = "Call store for pricing"

    products, warnings = validate_inventory_rows([row])

    assert len(products) == 1
    assert not hasattr(products[0], "sell_price")
    assert not warnings


def test_missing_required_column_raises_error() -> None:
    """Missing required spreadsheet columns should stop validation."""
    row = make_valid_row()
    row.pop("imageLinks")

    with pytest.raises(ValueError, match="imageLinks"):
        validate_inventory_rows([row])


def test_required_columns_do_not_include_private_fields() -> None:
    """WEBSITE LINK, APK, and Sell Price are not required columns."""
    assert "WEBSITE LINK" not in REQUIRED_COLUMNS
    assert "APK" not in REQUIRED_COLUMNS
    assert "Sell Price" not in REQUIRED_COLUMNS
