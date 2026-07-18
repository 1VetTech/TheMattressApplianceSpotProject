# The Mattress & Appliance Spot Inventory System

This project automatically turns the store's Google Sheets inventory into data that can be displayed on the GoDaddy website.

The goal is to keep inventory updates simple for store staff:

1. Open Google Sheets.
2. Add or update a product.
3. Set its Website Status to Published.
4. The automation handles the rest.

No Python, GitHub, or terminal knowledge is required for normal inventory updates.

## Current Project Status

The project can currently:

- Read the public inventory tab from Google Sheets.
- Include only products marked Published.
- Validate product information.
- Detect duplicate SKUs.
- Reject products with missing or invalid selling prices.
- Convert prices and quantities into website-ready values.
- Generate an inventory.json file.

The next stage will:

- Run the automation automatically through GitHub Actions.
- Publish inventory.json online.
- Connect the inventory to the GoDaddy website.
- Display searchable and filterable product cards.

## How the System Works

    InternalInventory
            |
            | Google Sheets formula
            v
    PublicWebsiteInventory
            |
            | Published as CSV
            v
    Python inventory automation
            |
            | Validation and cleanup
            v
    inventory.json
            |
            v
    GoDaddy website inventory section

## Google Sheets Tabs

### InternalInventory

This is the main working inventory sheet.

Store staff add and edit products here.

It may contain internal information that should not appear publicly, including:

- Manufacturer details
- Original prices
- Review notes
- Supplier information
- Other internal business notes

### PublicWebsiteInventory

This tab is generated automatically with a Google Sheets formula.

It contains only information approved for the website:

- SKU
- Category
- Item
- Sell Price
- Qty
- Description
- Image URL
- Color
- Website Status

Store staff should not type directly into this tab.

## Publishing a Product

To add a product to the website:

1. Open the InternalInventory tab.
2. Add or update the product row.
3. Enter a unique SKU.
4. Enter the product category.
5. Enter the item name.
6. Enter a valid Sell Price.
7. Add the quantity, description, color, and image URL when available.
8. Set Website Status to Published.

Products marked Draft or Hidden are not included in the public inventory.

## Required Product Fields

A published product must have:

- A unique SKU
- An item name
- A valid Sell Price
- Website Status set to Published

The automation allows missing image URLs and quantities for now, but it records warnings.

Products without images will eventually use an Image Coming Soon placeholder on the website.

## Project Structure

    TheMattressApplianceSpotProject/
    |
    |-- main.py
    |-- requirements.txt
    |-- .env.example
    |-- .gitignore
    |-- README.md
    |
    |-- inventory_automation/
    |   |-- __init__.py
    |   |-- config.py
    |   |-- exporter.py
    |   |-- models.py
    |   |-- sheets.py
    |   `-- validation.py
    |
    `-- tests/
        `-- test_validation.py

## What Each File Does

### main.py

Runs the full inventory process:

- Downloads the public CSV.
- Validates the rows.
- Displays warnings.
- Generates inventory.json.

### inventory_automation/config.py

Reads settings from the local .env file.

### inventory_automation/sheets.py

Downloads the published PublicWebsiteInventory CSV.

### inventory_automation/models.py

Defines the structure of a valid product.

### inventory_automation/validation.py

Checks product data before it reaches the website.

### inventory_automation/exporter.py

Creates the final JSON inventory file.

### tests/test_validation.py

Tests important validation rules.

## Local Developer Setup

### 1. Create a virtual environment

    py -m venv .venv
    .venv\Scripts\Activate.ps1

### 2. Install dependencies

    python -m pip install -r requirements.txt

### 3. Create the environment file

    Copy-Item .env.example .env

Open .env and enter the published CSV URL:

    PUBLIC_INVENTORY_CSV_URL="YOUR_PUBLISHED_CSV_URL"
    OUTPUT_JSON=output/inventory.json

The real .env file must never be committed to GitHub.

### 4. Run the tests

    python -m pytest -v

### 5. Run the inventory automation

    python main.py

The generated website data will be saved at:

    output/inventory.json

## Expected Warnings

The automation may display warnings such as:

    Row 2 (BED001) has no quantity.
    Row 2 (BED001) has no image URL.

These warnings do not stop the export.

The following problems do stop the export:

- Duplicate SKUs
- Missing selling prices
- Invalid selling prices
- Missing required CSV columns

## Security

Never commit these files or folders:

- .env
- credentials/
- .venv/
- output/

They are excluded by .gitignore.

The published Google Sheets tab must contain only information that is safe for website visitors to view.

Do not place passwords, private notes, supplier costs, employee information, or credentials in PublicWebsiteInventory.

## Planned Website Features

The GoDaddy inventory section will eventually include:

- Mobile-friendly product cards
- Search
- Category filters
- Color filters
- Price filtering
- Price sorting
- Product detail views
- Product images
- Availability
- Call Store button
- Get Directions button
- Financing message
- Image Coming Soon placeholders

## Repository Owner

GitHub account: 1VetTech

This repository supports the inventory system for The Mattress & Appliance Spot in LaGrange, Georgia.
