"""Data models used by the public inventory automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Product:  # pylint: disable=too-many-instance-attributes
    """Represents one validated website product."""

    sku: str
    category: str
    item: str
    quantity: int | None
    description: str
    image_url: str
    product_url: str
    color: str
    website_status: str

    def to_dict(self) -> dict[str, Any]:
        """Return approved customer-facing fields only.

        Product URL is retained internally for validation but is not
        included in the public inventory JSON.
        """
        return {
            "sku": self.sku,
            "category": self.category,
            "item": self.item,
            "quantity": self.quantity,
            "description": self.description,
            "image_url": self.image_url,
            "color": self.color,
            "website_status": self.website_status,
        }
