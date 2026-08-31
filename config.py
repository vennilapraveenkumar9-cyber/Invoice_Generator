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
FOOTERS_DIR = os.path.join(ASSETS_DIR, "footers")
WATERMARKS_DIR = os.path.join(ASSETS_DIR, "watermarks")

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
# Company profiles ("From" side of the invoice, logo, stamp, bank details).
#
# Both YSCC and Whiteness Cleaning are now built to match the *official*
# letterhead files the company sent (LETTER_HEAD_WCS.docx and
# YSCC_NEW_LTRHEAD2024.docx) pixel-for-pixel: the exact logo graphic, the
# exact footer band graphic, and (for YSCC) the exact faint background
# watermark shape -- all extracted directly from those files rather than
# redrawn/approximated.
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
        "invoice_title": "TAX INVOICE",
        # YSCC keeps the original layout: small logo top-left + contact
        # info (Contact/Email/CR) printed top-right by our code -- this
        # matches the official letterhead exactly (logo + text, not a
        # single flattened banner image).
        "header_style": "standard",
        # Exact footer band image extracted from the official letterhead
        # (navy bar, left-aligned tagline, white icon, red accent block)
        # instead of a code-drawn rectangle -- pixel-identical to the
        # letterhead file.
        "footer_image_path": os.path.join(FOOTERS_DIR, "yscc.png"),
        # Faint decorative watermark shape from the official letterhead,
        # extracted with a transparent background. Drawn low-opacity in
        # the lower part of the page, behind all text/tables.
        "watermark_path": os.path.join(WATERMARKS_DIR, "yscc.png"),
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
        "invoice_title": "INVOICE",
        # The logo file for Whiteness IS the full official letterhead
        # banner (logo + Arabic/English name + contact block on both
        # sides), extracted directly from the company's docx -- so it's
        # centered and stretched across the top, with no separate
        # code-generated contact text next to it.
        "header_style": "banner",
        # Exact footer band image from the official letterhead (red line
        # + indigo bar + centered white tagline text).
        "footer_image_path": os.path.join(FOOTERS_DIR, "whiteness.png"),
        "watermark_path": None,
    },
}

# ---------------------------------------------------------------------------
# Preset "Billed To" clients. These are independent of which company issues
# the invoice -- e.g. "Ebrahim Ali Trading Co W.L.L" was originally seen as
# a client on an Al Jameel invoice, but the address itself is just client
# data and stays available here for billing from any company, even though
# Al Jameel is no longer offered as an issuing company profile above.
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
    # Al Jameel Tower Construction & Trading itself is no longer offered as
    # an issuing company, but its own address/VAT/CR is kept here as a
    # billable client in case either remaining company ever invoices them.
    "Al Jameel Tower Construction & Trading": {
        "name": "M/S. Al Jameel Tower Construction & Trading",
        "address_lines": [
            "Flat/Shop No: -0, Building No: -12, Road/Street No: -58, Buri",
            "Block No: -756, Kingdom of Bahrain",
        ],
        "cr": "27387-3",
        "vat": "220004058200002",
    },
}

NEW_CLIENT_LABEL = "+ New client (type address manually)"
CUSTOM_LOGO_LABEL = "Upload my own logo"
CUSTOM_STAMP_LABEL = "Upload my own stamp"
NO_STAMP_LABEL = "No stamp"

CURRENCY = "BHD"
DEFAULT_VAT_PERCENT = 10.0

# Sampled from the original invoices' scanned paper (very close to white,
# with the faintest warm-gray cast) so generated PDFs match the paper tone.
PAGE_BACKGROUND_COLOR = "#FDFDFB"
