"""Validation and normalization for public inventory rows."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from inventory_automation.models import Product


REQUIRED_COLUMNS = {
    "SKU",
    "Category",
    "Item",
    "Sell Price",
    "Qty",
    "Description",
    "Image URL",
    "Color",
    "Website Status",
}


def validate_inventory_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[Product], list[str]]:
    """Validate public inventory rows and create Product objects.

    Only rows marked Published are accepted. Duplicate SKUs or missing
    required columns stop the export because they could corrupt the website
    catalog.

    Args:
        rows: Raw rows downloaded from the published CSV.

    Returns:
        A tuple containing validated products and warning messages.

    Raises:
        ValueError: If required columns are missing, duplicate SKUs exist,
            or a published product has no valid selling price.
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

        # The public tab should already contain only Published rows,
        # but this extra check prevents accidental exposure.
        if status.lower() != "published":
            warnings.append(
                f"Row {row_number} was skipped because Website Status "
                f"is {status!r}, not 'Published'."
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

        sell_price = _parse_decimal(
            row.get("Sell Price"),
            row_number,
            "Sell Price",
            warnings,
        )

        if sell_price is None:
            raise ValueError(
                f"Row {row_number} ({sku}) cannot be published without "
                "a valid Sell Price."
            )

        quantity = _parse_integer(
            row.get("Qty"),
            row_number,
            "Qty",
            warnings,
        )

        category = _clean_text(row.get("Category"))
        description = _clean_text(row.get("Description"))
        image_url = _clean_text(row.get("Image URL"))
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

        if not image_url:
            warnings.append(
                f"Row {row_number} ({sku}) has no image URL."
            )

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

    if amount < 0:
        warnings.append(
            f"Row {row_number} has a negative {field_name}: {value!r}."
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
