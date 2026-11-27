
"""JSON export helpers for validated inventory data."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inventory_automation.models import Product


PUBLIC_FIELDS = {
    "sku",
    "category",
    "item",
    "quantity",
    "description",
    "image_url",
    "color",
    "website_status",
}


def _product_to_public_dict(product: Product) -> dict[str, Any]:
    """Return only approved customer-facing product fields."""
    product_data = product.to_dict()

    return {
        field: product_data[field]
        for field in PUBLIC_FIELDS
        if field in product_data
    }


def write_inventory_json(
    products: list[Product],
    output_path: Path,
) -> None:
    """Write validated products to a public website JSON file."""
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
