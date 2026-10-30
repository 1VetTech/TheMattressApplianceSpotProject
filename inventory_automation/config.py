"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Stores configuration for the inventory automation.

    Attributes:
        public_inventory_csv_url: Public CSV URL for website inventory.
        output_json: Path where generated inventory JSON is saved.
    """

    public_inventory_csv_url: str
    output_json: Path

    @classmethod
    def from_environment(cls) -> Settings:
        """Load application settings from the local environment.

        Returns:
            A populated Settings instance.

        Raises:
            ValueError: If the public inventory CSV URL is missing.
        """
        load_dotenv()

        csv_url = os.getenv(
            "PUBLIC_INVENTORY_CSV_URL",
            "",
        ).strip()

        output_json = Path(
            os.getenv(
                "OUTPUT_JSON",
                "output/inventory.json",
            ).strip()
        )

        if not csv_url or "PASTE_YOUR" in csv_url:
            raise ValueError(
                "Add the published inventory CSV URL to the .env file."
            )

        return cls(
            public_inventory_csv_url=csv_url,
            output_json=output_json,
        )
