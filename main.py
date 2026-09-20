"""
main.py

Generate website inventory JSON from the published inventory CSV.
"""

from __future__ import annotations

import logging
import sys
import warnings

from inventory_automation.config import Settings
from inventory_automation.exporter import write_inventory_json
from inventory_automation.sheets import fetch_inventory_rows
from inventory_automation.validation import validate_inventory_rows


# ==========================================================
# WARNING CONFIGURATION
# ==========================================================

# Suppress non-critical warnings.
warnings.filterwarnings("ignore")


# ==========================================================
# LOGGING
# ==========================================================

def configure_logging() -> None:
    """
    Configure application logging.

    Change INFO to ERROR if you only want to
    see failures in production.
    """

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
    validate products, and generate the
    website inventory JSON file.

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
        # Validation
        # ------------------------------------------

        products, warning_messages = validate_inventory_rows(rows)

        if warning_messages:
            logger.warning(
                "Validation completed with %d warning(s).",
                len(warning_messages),
            )

            for message in warning_messages:
                logger.warning(message)

        # ------------------------------------------
        # Export JSON
        # ------------------------------------------

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