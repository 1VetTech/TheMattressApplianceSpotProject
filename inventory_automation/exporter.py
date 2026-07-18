"""JSON export helpers for validated inventory data."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inventory_automation.models import Product


def _product_to_public_dict(product: Product) -> dict[str, Any]:
    """Convert a product into customer-facing website data.

    Internal review notes are intentionally excluded from the public JSON.

    Args:
        product: Validated inventory product.

    Returns:
        A JSON-compatible dictionary containing public product fields.
    """
    product_data = product.to_dict()
    product_data.pop("review_notes", None)
    return product_data


def write_inventory_json(
    products: list[Product],
    output_path: Path,
) -> None:
    """Write validated products to a public website JSON file.

    The completed data is first written to a temporary file. The temporary
    file replaces the website JSON only after writing succeeds.

    Args:
        products: Validated inventory products.
        output_path: Destination path for the generated JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "product_count": len(products),
        "products": [
            _product_to_public_dict(product)
            for product in products
        ],
    }

    temporary_path = output_path.with_suffix(".tmp")

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(output_path)
