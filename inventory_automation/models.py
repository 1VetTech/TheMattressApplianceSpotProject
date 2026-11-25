
"""Data models used by the public inventory automation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Product:
    """Represents one validated website product.

    Attributes:
        sku: Unique product identifier.
        category: Main website category.
        item: Customer-facing product name.
        sell_price: Current customer-facing price, if confirmed.
        quantity: Number of units available, when known.
        description: Customer-facing product description.
        image_url: Public product image URL.
        product_url: Ashley Furniture product page URL.
        color: Product color or finish.
        website_status: Publishing status from the spreadsheet.
    """

    sku: str
    category: str
    item: str
    sell_price: Decimal | None
    quantity: int | None
    description: str
    image_url: str
    product_url: str
    color: str
    website_status: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the product into JSON-compatible data.

        Returns:
            A dictionary ready to be written to inventory.json.
            An unavailable price is represented as None, which becomes
            JSON null.
        """
        result = asdict(self)

        if self.sell_price is not None:
            result["sell_price"] = float(self.sell_price)
        else:
            result["sell_price"] = None

        return result
