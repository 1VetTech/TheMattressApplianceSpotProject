
"""
main.py

Generate website inventory JSON from the published inventory CSV.
"""

from __future__ import annotations

import logging
import sys

from inventory_automation.config import Settings
from inventory_automation.exporter import write_inventory_json
from inventory_automation.sheets import fetch_inventory_rows
from inventory_automation.validation import (
    check_product_urls,
    validate_inventory_rows,
)


# ==========================================================
# LOGGING
# ==========================================================

def configure_logging() -> None:
    """Configure application logging."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


# ==========================================================
# MAIN PROCESS
# ==========================================================

def run() -> int:
    """
    Download the published inventory CSV,
    validate products and URLs, and generate
    website inventory JSON.

    Returns:
        0 = Success
        1 = Failure
    """

    configure_logging()

    logger = logging.getLogger(__name__)

    try:
        # ------------------------------------------
        # Load Settings
        # ------------------------------------------

        settings = Settings.from_environment()

        logger.info(
            "Downloading published inventory CSV..."
        )

        # ------------------------------------------
        # Download Inventory
        # ------------------------------------------

        rows = fetch_inventory_rows(settings)

        logger.info(
            "Retrieved %d inventory rows.",
            len(rows),
        )

        # ------------------------------------------
        # Spreadsheet Validation
        # ------------------------------------------

        logger.info(
            "Validating inventory products..."
        )

        products, warning_messages = validate_inventory_rows(rows)

        logger.info(
            "Validated %d publishable product(s).",
            len(products),
        )

        # ------------------------------------------
        # Live URL Verification
        # ------------------------------------------

        logger.info(
            "Checking product image and product-page URLs..."
        )

        url_warnings = check_product_urls(
            products,
            timeout=8,
        )

        warning_messages.extend(url_warnings)

        logger.info(
            "Live URL verification completed with %d warning(s).",
            len(url_warnings),
        )

        # ------------------------------------------
        # Warning Report
        # ------------------------------------------

        if warning_messages:
            logger.warning(
                "Inventory processing completed with %d warning(s).",
                len(warning_messages),
            )

            for message in warning_messages:
                logger.warning(message)

        else:
            logger.info(
                "No inventory or URL warnings detected."
            )

        # ------------------------------------------
        # Export JSON
        # ------------------------------------------

        logger.info(
            "Generating website inventory JSON..."
        )

        write_inventory_json(
            products,
            settings.output_json,
        )

        logger.info(
            "Successfully exported %d product(s) to %s",
            len(products),
            settings.output_json,
        )

        return 0

    except FileNotFoundError as error:
        logger.error(
            "Required file not found: %s",
            error,
        )
        return 1

    except ModuleNotFoundError as error:
        logger.error(
            "Missing dependency: %s",
            error,
        )

        logger.error(
            "Run: pip install -r requirements.txt"
        )

        return 1

    except (ValueError, TypeError, OSError) as error:
        logger.exception(
            "Inventory processing failed: %s",
            error,
        )
        return 1


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    sys.exit(run())
