"""Generate website inventory JSON from the published inventory CSV."""

from __future__ import annotations

import logging
import sys

from inventory_automation.config import Settings
from inventory_automation.exporter import write_inventory_json
from inventory_automation.sheets import fetch_inventory_rows
from inventory_automation.validation import validate_inventory_rows


def configure_logging() -> None:
    """Configure readable terminal logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def run() -> int:
    """Run the complete public inventory export process.

    Returns:
        Zero when the export succeeds; otherwise, one.
    """
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        settings = Settings.from_environment()

        logger.info("Downloading published inventory CSV.")

        rows = fetch_inventory_rows(settings)

        logger.info(
            "Read %d published inventory rows.",
            len(rows),
        )

        products, warnings = validate_inventory_rows(rows)

        for warning in warnings:
            logger.warning(warning)

        write_inventory_json(
            products,
            settings.output_json,
        )

        logger.info(
            "Exported %d public products to %s.",
            len(products),
            settings.output_json,
        )

        return 0

    except Exception:
        logger.exception("Public inventory export failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run())
