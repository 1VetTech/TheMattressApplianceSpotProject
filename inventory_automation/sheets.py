"""Published Google Sheets CSV access helpers."""

from __future__ import annotations

import csv
import io
from typing import Any

import requests

from inventory_automation.config import Settings


def fetch_inventory_rows(
    settings: Settings,
) -> list[dict[str, Any]]:
    """Download public inventory rows from the published CSV.

    This reader does not require Google OAuth credentials. It can only access
    the PublicWebsiteInventory tab that was deliberately published.

    Args:
        settings: Configuration containing the published CSV URL.

    Returns:
        A list of nonempty inventory rows keyed by column header.

    Raises:
        requests.HTTPError: If the CSV cannot be downloaded.
        ValueError: If the response is empty or has no headers.
    """
    response = requests.get(
        settings.public_inventory_csv_url,
        timeout=30,
    )
    response.raise_for_status()

    csv_text = response.text.lstrip("\ufeff").strip()

    if not csv_text:
        raise ValueError("The published inventory CSV is empty.")

    reader = csv.DictReader(io.StringIO(csv_text))

    if not reader.fieldnames:
        raise ValueError("The published inventory CSV has no headers.")

    rows: list[dict[str, Any]] = []

    for row in reader:
        cleaned_row = {
            str(header).strip(): str(value or "").strip()
            for header, value in row.items()
            if header and str(header).strip()
        }

        if any(cleaned_row.values()):
            rows.append(cleaned_row)

    return rows
