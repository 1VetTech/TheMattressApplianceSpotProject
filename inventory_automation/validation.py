
"""Validation and normalization for public inventory rows."""

from __future__ import annotations

from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from inventory_automation.models import Product


# WEBSITE LINK is intentionally optional.
# Sell Price and APK are not required or processed.
REQUIRED_COLUMNS = {
    "SKU",
    "Category",
    "Item",
    "Qty",
    "imageLinks",
    "Description",
    "Color",
    "Website Status",
}


# pylint: disable=too-many-locals, too-many-branches
def validate_inventory_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[Product], list[str]]:
    """Validate public inventory rows and create Product objects.

    Only rows marked Publish or Published are accepted.

    WEBSITE LINK is optional. When supplied, it is checked and
    retained internally for URL verification.

    Sell Price and APK are intentionally ignored.

    Duplicate SKUs or missing required columns stop the export.

    Args:
        rows: Raw rows downloaded from the public inventory CSV.

    Returns:
        Validated products and warning messages.

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
        product, row_warnings = _validate_inventory_row(
            row,
            row_number,
            seen_skus,
        )
        warnings.extend(row_warnings)

        if product is not None:
            products.append(product)

    return products, warnings


def _validate_inventory_row(
    row: dict[str, Any],
    row_number: int,
    seen_skus: set[str],
) -> tuple[Product | None, list[str]]:
    """Validate row identity before building a product."""
    status = _clean_text(row.get("Website Status"))

    if status.lower() not in {"publish", "published"}:
        return None, [
            f"Row {row_number} was skipped because Website Status "
            f"is {status!r}, not 'Publish' or 'Published'."
        ]

    sku = _clean_text(row.get("SKU")).upper()
    item = _clean_text(row.get("Item"))

    if not sku:
        return None, [
            f"Row {row_number} was skipped because SKU is blank."
        ]

    if not item:
        return None, [
            f"Row {row_number} ({sku}) was skipped because Item is blank."
        ]

    if sku in seen_skus:
        raise ValueError(
            f"Duplicate SKU found on row {row_number}: {sku}"
        )

    seen_skus.add(sku)

    return _build_product(row, row_number, sku, item, status)


def _build_product(
    row: dict[str, Any],
    row_number: int,
    sku: str,
    item: str,
    status: str,
) -> tuple[Product, list[str]]:
    """Build a Product object and collect validation warnings."""
    warnings: list[str] = []

    quantity = _parse_integer(
        row.get("Qty"),
        row_number,
        "Qty",
        warnings,
    )

    category = _clean_text(row.get("Category"))
    description = _clean_text(row.get("Description"))
    image_url = _clean_text(row.get("imageLinks"))

    # WEBSITE LINK is optional. APK is not used.
    product_url = _clean_text(row.get("WEBSITE LINK"))

    color = _clean_text(row.get("Color"))

    warnings.extend(
        _validate_optional_fields(
            row_number,
            sku,
            row,
            quantity,
        )
    )

    image_url, product_url, url_warnings = _validate_product_links(
        row_number,
        sku,
        image_url,
        product_url,
    )
    warnings.extend(url_warnings)

    product = Product(
        sku=sku,
        category=category,
        item=item,
        quantity=quantity,
        description=description,
        image_url=image_url,
        product_url=product_url,
        color=color,
        website_status=status,
    )

    return product, warnings


def _validate_optional_fields(
    row_number: int,
    sku: str,
    row: dict[str, Any],
    quantity: int | None,
) -> list[str]:
    """Create warnings for missing optional product fields."""
    warnings: list[str] = []

    missing_fields = (
        (not _clean_text(row.get("Category")), "has no category."),
        (quantity is None, "has no quantity."),
        (not _clean_text(row.get("Description")), "has no description."),
        (not _clean_text(row.get("Color")), "has no color."),
    )

    for is_missing, message in missing_fields:
        if is_missing:
            warnings.append(f"Row {row_number} ({sku}) {message}")

    return warnings


def _validate_product_links(
    row_number: int,
    sku: str,
    image_url: str,
    product_url: str,
) -> tuple[str, str, list[str]]:
    """Validate the required image and optional product-page URLs."""
    warnings: list[str] = []

    image_url, image_warnings = _validate_url_field(
        image_url,
        row_number,
        sku,
        "imageLinks URL",
        "imageLinks URL",
    )
    warnings.extend(image_warnings)

    # Only validate WEBSITE LINK when a value is supplied.
    # A blank WEBSITE LINK is allowed and creates no warning.
    if product_url:
        product_url, product_warnings = _validate_url_field(
            product_url,
            row_number,
            sku,
            "WEBSITE LINK",
            "WEBSITE LINK URL",
        )
        warnings.extend(product_warnings)

    return image_url, product_url, warnings


def _validate_url_field(
    value: str,
    row_number: int,
    sku: str,
    missing_label: str,
    invalid_label: str,
) -> tuple[str, list[str]]:
    """Validate a URL's presence and HTTPS structure."""
    if not value:
        return "", [
            f"Row {row_number} ({sku}) has no {missing_label}."
        ]

    if not _is_valid_https_url(value):
        return "", [
            f"Row {row_number} ({sku}) has an invalid "
            f"{invalid_label}: {value!r}"
        ]

    return value, []


def check_product_urls(
    products: list[Product],
    timeout: int = 8,
) -> list[str]:
    """Check image URLs and optional product-page URLs.

    URL failures create warnings. They do not remove products or
    stop the inventory export.
    """
    warnings: list[str] = []

    for product in products:
        if product.image_url:
            success, detail, content_type = _check_remote_url(
                product.image_url,
                timeout,
            )

            if not success:
                warnings.append(
                    f"{product.sku}: Image URL check failed: {detail}"
                )
            elif not content_type.startswith("image/"):
                warnings.append(
                    f"{product.sku}: Image URL returned unexpected "
                    f"content type: {content_type or 'unknown'}"
                )

        # Check the Ashley product page only when supplied.
        if product.product_url:
            success, detail, _ = _check_remote_url(
                product.product_url,
                timeout,
            )

            if not success:
                warnings.append(
                    f"{product.sku}: WEBSITE LINK check failed: {detail}"
                )

    return warnings


def _check_remote_url(
    url: str,
    timeout: int,
) -> tuple[bool, str, str]:
    """Request a remote URL and return status and content type."""
    request = Request(
        url,
        headers={
            "User-Agent": "1VETTECH-Inventory-Validator/1.0",
            "Range": "bytes=0-1023",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            final_url = response.geturl()

            content_type = response.headers.get(
                "Content-Type",
                "",
            ).split(";")[0].strip().lower()

            if urlsplit(final_url).scheme.lower() != "https":
                return (
                    False,
                    "Redirected to a non-HTTPS address.",
                    content_type,
                )

            if not 200 <= status < 300:
                return (
                    False,
                    f"HTTP status {status}.",
                    content_type,
                )

            return True, f"HTTP status {status}.", content_type

    except HTTPError as error:
        return False, f"HTTP status {error.code}.", ""

    except (URLError, TimeoutError, OSError, ValueError) as error:
        return False, str(error), ""


def _clean_text(value: Any) -> str:
    """Normalize a spreadsheet value into trimmed text."""
    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def _is_valid_https_url(value: str) -> bool:
    """Check URL structure and require HTTPS.

    This does not confirm that the remote page or image exists.
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
