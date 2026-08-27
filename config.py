"""
config.py
---------
Static configuration for the Invoice Generator: company profiles, preset
billed-to clients, and app-wide constants/limits.

Keeping this data separate from app.py makes it easy to add a new company
or a new saved client address without touching any UI or PDF-generation
logic.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")
STAMPS_DIR = os.path.join(ASSETS_DIR, "stamps")

# ---------------------------------------------------------------------------
# Security / sanity limits (also enforced again in security.py)
# ---------------------------------------------------------------------------
MAX_UPLOAD_MB = 3                      # max size for a user-uploaded logo/stamp
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"png", "jpg", "jpeg"}
MAX_ITEM_ROWS = 40                     # cap on invoice line items
MAX_EXTRA_COLUMNS = 5                  # cap on custom extra columns in the table
MAX_TEXT_LEN = 500                     # cap on any single free-text field
MAX_MULTILINE_LEN = 1500               # cap on address / notes blocks

# ---------------------------------------------------------------------------
# Company profiles ("From" side of the invoice, logo, stamp, bank details)
# ---------------------------------------------------------------------------
COMPANIES = {
    "yscc": {
        "display_name": "YSCC Cleaning & Contracting Company",
        "legal_name": "Yaqoob Sons Contracting Company",
        "logo_path": os.path.join(LOGOS_DIR, "yscc.png"),
        "stamp_path": os.path.join(STAMPS_DIR, "yscc.png"),
        "address_lines": [
            "Building: -802, Road: -415, Town Salmabad",
            "Block: -704, Kingdom of Bahrain",
        ],
        "vat": "220003980800002",
        "cr": "95318-1",
        "contact": "+973 3399 7124 / +973 3694 0169",
        "email": "ysccbahrain@gmail.com",
        "account_name": "Yaqoob sons contracting company",
        "iban": "BH53FIBH11000487340001",
        "footer_tagline": "General Cleaning | Carpet / Sofa Shampooing | Marble Polishing | "
                           "Water Tank Cleaning | Facade Cleaning | etc.",
        "brand_color": "#D81F42",
        "invoice_title": "TAX INVOICE",
    },
    "aljameel": {
        "display_name": "Al Jameel Tower Construction & Trading",
        "legal_name": "Al Jameel Tower Construction & Trading",
        "logo_path": os.path.join(LOGOS_DIR, "aljameel.png"),
        "stamp_path": os.path.join(STAMPS_DIR, "aljameel.png"),
        "address_lines": [
            "Flat/Shop No: -0, Building No: -12, Road/Street No: -58, Buri",
            "Block No: -756, Kingdom of Bahrain",
        ],
        "vat": "220004058200002",
        "cr": "27387-3, RD: 58, Bld: 12, Blk: 756 BURI",
        "contact": "33569858 / 38736809",
        "email": "aljameeltc@gmail.com",
        "account_name": "Al Jameel Tower Construction & Trading",
        "iban": "BH63BIBB00100000100082",
        "footer_tagline": "",
        "brand_color": "#1789C9",
        "invoice_title": "TAX INVOICE",
    },
    "whiteness": {
        "display_name": "Whiteness Cleaning",
        "legal_name": "Whiteness Cleaning",
        "logo_path": os.path.join(LOGOS_DIR, "whiteness.png"),
        "stamp_path": os.path.join(STAMPS_DIR, "whiteness.png"),
        "address_lines": [
            "Building 1172, Road 5443, Buri",
            "Block 754, Kingdom of Bahrain",
        ],
        "vat": "",
        "cr": "145647-2",
        "contact": "38214676",
        "email": "whiteness2023jameel@gmail.com",
        "account_name": "Whiteness Cleaning",
        "iban": "BH63 ALSA 0025 5773 1001 00",
        "footer_tagline": "",
        "brand_color": "#E23054",
        "invoice_title": "INVOICE",
    },
}

# ---------------------------------------------------------------------------
# Preset "Billed To" clients, extracted from historical sample invoices.
# The user can still choose "+ New client" and type a fresh address.
# ---------------------------------------------------------------------------
PRESET_CLIENTS = {
    "SMA Solutions W.L.L": {
        "name": "M/S. SMA SOLUTIONS WLL",
        "address_lines": [
            "Flat/shop no: 317, Building: 75,",
            "Road: 3201, Block: 332, Area: BUASHIRAH",
            "Kingdom of Bahrain.",
        ],
        "cr": "166616-1",
        "vat": "",
    },
    "Tech Bay IT Solutions W.L.L": {
        "name": "M/S. TECH BAY IT SOLUTIONS W.L.L",
        "address_lines": [
            "Flat/Shop: -22, Building: -583,",
            "Road/Street: -1207, Town: -AL Ramli,",
            "Block: 712, Kingdom of Bahrain.",
        ],
        "cr": "106913-1",
        "vat": "220010032900002",
    },
    "Ebrahim Ali Trading Co W.L.L": {
        "name": "M/S. Ebrahim Ali Trading co W.L.L",
        "address_lines": [
            "Flat/Shop No: -0, Building: -1950,",
            "Road/Street No: -585, Mahazzah, Block 603,",
            "Kingdom of Bahrain",
        ],
        "cr": "10190-2",
        "vat": "200011236300002",
    },
    "Palletbiz W.L.L": {
        "name": "M/S. Palletbiz W.L.L",
        "address_lines": [
            "Flat/Shop: -12, Building: -2401,",
            "Road/Street: -3634, Block: -636,",
            "Kingdom of Bahrain.",
        ],
        "cr": "",
        "vat": "220011428800002",
    },
    "Easy Lease Motorcycle Rental W.L.L": {
        "name": "M/S. EASY LEASE MOTORCYCLE RENTAL W.L.L.",
        "address_lines": [
            "Flat/Shop No: -2296, Building: -2296,",
            "Road/Street No: -439, Salmabad,",
            "Block: -704, Kingdom of Bahrain.",
        ],
        "cr": "153808-1",
        "vat": "220018828200002",
    },
    "Season International Trading & Industries Co": {
        "name": "M/S. Season international Trading & Industries Co",
        "address_lines": [
            "Building: -477, Road: -109, Town Sitra",
            "Block: -601, Kingdom of Bahrain",
        ],
        "cr": "",
        "vat": "200010112700002",
    },
}

NEW_CLIENT_LABEL = "+ New client (type address manually)"
CUSTOM_LOGO_LABEL = "Upload my own logo"
CUSTOM_STAMP_LABEL = "Upload my own stamp"
NO_STAMP_LABEL = "No stamp"

CURRENCY = "BHD"
DEFAULT_VAT_PERCENT = 10.0
