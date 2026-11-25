
"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class Settings:
    """Stores configuration for inventory automation."""

    public_inventory_csv_url: str
    output_json: Path

    @classmethod
    def from_environment(cls) -> Settings:
        """Load settings from environment variables or local .env."""

        # Load .env only when available.
        # Existing environment variables take priority.
        if ENV_FILE.is_file():
            load_dotenv(
                dotenv_path=ENV_FILE,
                override=False,
            )

        # GitHub Actions Secrets are exposed as environment variables.
        csv_url = os.getenv(
            "PUBLIC_INVENTORY_CSV_URL",
            "",
        ).strip()

        if not csv_url:
            raise ValueError(
                "PUBLIC_INVENTORY_CSV_URL is missing.\n"
                "Configure it as a GitHub Actions environment variable "
                "or GitHub Repository Secret.\n"
                "For local development, you may use a .env file."
            )

        # Reject placeholder values.
        placeholders = (
            "PASTE_YOUR",
            "REPLACE_WITH",
            "YOUR_PUBLISHED_ID",
            "YOUR_GOOGLE_SHEET",
        )

        if any(value in csv_url.upper() for value in placeholders):
            raise ValueError(
                "The published inventory CSV URL still contains "
                "a placeholder. Configure the actual published CSV URL."
            )

        # Validate Google Sheets URL structure.
        try:
            parsed = urlsplit(csv_url)

            valid_url = (
                parsed.scheme.lower() == "https"
                and parsed.hostname == "docs.google.com"
                and parsed.path.startswith("/spreadsheets/")
                and not parsed.username
                and not parsed.password
                and not any(char.isspace() for char in csv_url)
            )

        except ValueError:
            valid_url = False

        if not valid_url:
            raise ValueError(
                "PUBLIC_INVENTORY_CSV_URL must be a valid "
                "Google Sheets HTTPS URL."
            )

        # Load output location.
        output_value = os.getenv(
            "OUTPUT_JSON",
            "output/inventory.json",
        ).strip()

        if not output_value:
            output_value = "output/inventory.json"

        output_json = Path(output_value)

        if not output_json.is_absolute():
            output_json = PROJECT_ROOT / output_json

        return cls(
            public_inventory_csv_url=csv_url,
            output_json=output_json,
        )
