
"""Validation and normalization for public inventory rows."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit

from inventory_automation.models import Product


REQUIRED_COLUMNS = {
    "SKU",
    "Category",
    "Item",
    "Sell Price",
    "Qty",
    "Description",
    "imageLinks",
    "APK",
    "Color",
    "Website Status",
}


def validate_inventory_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[Product], list[str]]:
    """Validate public inventory rows and create Product objects.

    Only rows marked Publish or Published are accepted.

    Missing or unavailable selling prices are allowed. The website
    should display Coming Soon when sell_price is None.

    Duplicate SKUs or missing required columns stop the export.

    Args:
        rows: Raw rows downloaded from the public inventory CSV.

    Returns:
        A tuple containing validated products and warning messages.

    Raises:
        ValueError: If required columns are missing or duplicate SKUs exist.
    """
    if not rows:
        return [], ["The public inventory contains no rows."]

    missing_columns = REQUIRED_COLUMNS.difference(rows[0].keys())

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"The public inventory is missing columns: {missing}"
        )

    products: list[Product] = []
    warnings: list[str] = []
    seen_skus: set[str] = set()

    for row_number, row in enumerate(rows, start=2):
        status = _clean_text(row.get("Website Status"))

        # Accept both spreadsheet status formats.
        if status.lower() not in {"publish", "published"}:
            warnings.append(
                f"Row {row_number} was skipped because Website Status "
                f"is {status!r}, not 'Publish' or 'Published'."
            )
            continue

        sku = _clean_text(row.get("SKU")).upper()
        item = _clean_text(row.get("Item"))

        if not sku:
            warnings.append(
                f"Row {row_number} was skipped because SKU is blank."
            )
            continue

        if not item:
            warnings.append(
                f"Row {row_number} ({sku}) was skipped because Item is blank."
            )
            continue

        if sku in seen_skus:
            raise ValueError(
                f"Duplicate SKU found on row {row_number}: {sku}"
            )

        seen_skus.add(sku)

        # Missing or invalid prices no longer stop the export.
        sell_price = _parse_decimal(
            row.get("Sell Price"),
            row_number,
            "Sell Price",
            warnings,
        )

        if sell_price is None or sell_price == 0:
            warnings.append(
                f"Row {row_number} ({sku}) has no confirmed selling price. "
                "Website should display Coming Soon."
            )
            sell_price = None

        quantity = _parse_integer(
            row.get("Qty"),
            row_number,
            "Qty",
            warnings,
        )

        category = _clean_text(row.get("Category"))
        description = _clean_text(row.get("Description"))
        image_url = _clean_text(row.get("imageLinks"))
        product_url = _clean_text(row.get("APK"))
        color = _clean_text(row.get("Color"))

        if not category:
            warnings.append(
                f"Row {row_number} ({sku}) has no category."
            )

        if quantity is None:
            warnings.append(
                f"Row {row_number} ({sku}) has no quantity."
            )

        if not description:
            warnings.append(
                f"Row {row_number} ({sku}) has no description."
            )

        # Validate image URL.
        if not image_url:
            warnings.append(
                f"Row {row_number} ({sku}) has no imageLinks URL."
            )
        elif not _is_valid_https_url(image_url):
            warnings.append(
                f"Row {row_number} ({sku}) has an invalid imageLinks URL: "
                f"{image_url!r}"
            )
            image_url = ""

        # Validate Ashley product page URL.
        if not product_url:
            warnings.append(
                f"Row {row_number} ({sku}) has no APK product URL."
            )
        elif not _is_valid_https_url(product_url):
            warnings.append(
                f"Row {row_number} ({sku}) has an invalid APK URL: "
                f"{product_url!r}"
            )
            product_url = ""

        if not color:
            warnings.append(
                f"Row {row_number} ({sku}) has no color."
            )

        products.append(
            Product(
                sku=sku,
                category=category,
                item=item,
                sell_price=sell_price,
                quantity=quantity,
                description=description,
                image_url=image_url,
                product_url=product_url,
                color=color,
                website_status=status,
            )
        )

    return products, warnings


def _clean_text(value: Any) -> str:
    """Normalize a spreadsheet value into trimmed text."""
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def _is_valid_https_url(value: str) -> bool:
    """Check URL structure and require HTTPS.

    This does not confirm that the remote page or image actually exists.
    """
    try:
        parsed = urlsplit(value)

        return (
            parsed.scheme.lower() == "https"
            and bool(parsed.hostname)
            and "." in parsed.hostname
            and not parsed.username
            and not parsed.password
            and not any(char.isspace() for char in value)
        )
    except ValueError:
        return False


def _parse_decimal(
    value: Any,
    row_number: int,
    field_name: str,
    warnings: list[str],
) -> Decimal | None:
    """Parse a nonnegative currency value."""
    text = _clean_text(value)
    text = text.replace("$", "").replace(",", "")

    if not text:
        return None

    try:
        amount = Decimal(text)
    except InvalidOperation:
        warnings.append(
            f"Row {row_number} has an invalid {field_name}: {value!r}."
        )
        return None

    if not amount.is_finite() or amount < 0:
        warnings.append(
            f"Row {row_number} has an invalid or negative "
            f"{field_name}: {value!r}."
        )
        return None

    return amount


def _parse_integer(
    value: Any,
    row_number: int,
    field_name: str,
    warnings: list[str],
) -> int | None:
    """Parse a nonnegative whole-number quantity."""
    text = _clean_text(value)

    if not text:
        return None

    try:
        number = int(text)
    except ValueError:
        warnings.append(
            f"Row {row_number} has an invalid {field_name}: {value!r}."
        )
        return None

    if number < 0:
        warnings.append(
            f"Row {row_number} has a negative {field_name}: {value!r}."
        )
        return None

    return number
