"""
app.py
------
Streamlit front-end for the Invoice Generator.

Flow:
  1. Pick a company profile (logo / stamp / bank details auto-fill, all editable).
  2. Pick a "Billed To" client from presets, or add a new one.
  3. Fill invoice meta (date, invoice no, LPO, payment terms).
  4. Build the line-items table (dynamic rows + optional extra columns);
     VAT and totals are computed automatically.
  5. Preview totals, then generate & download the PDF.

Security notes (see security.py for the implementation):
  - All text fields are length-capped and control-character-stripped.
  - All text is XML-escaped before being placed into the PDF (ReportLab
    Paragraphs use a small XML markup language, so raw user text could
    otherwise break layout or inject markup).
  - Uploaded logo/stamp images are validated (type, size, real image
    content) and re-encoded through Pillow before use -- the original
    uploaded bytes are never written to disk or passed through untouched.
  - Row/column counts and numeric fields are clamped to sane ranges to
    prevent pathological/oversized PDFs.
  - Optional app-wide access code via st.secrets (disabled unless you
    configure it) -- see README.md.
  - Generated PDFs are built in-memory (io.BytesIO) and never written to
    a predictable path on disk.
"""

import datetime
import io

import streamlit as st

from config import (
    COMPANIES, PRESET_CLIENTS, NEW_CLIENT_LABEL, CUSTOM_LOGO_LABEL,
    CUSTOM_STAMP_LABEL, NO_STAMP_LABEL, MAX_ITEM_ROWS, MAX_EXTRA_COLUMNS,
    DEFAULT_VAT_PERCENT, CURRENCY,
)
from security import (
    clean_text, clean_multiline, validate_uploaded_image, ValidationError,
    safe_filename, bounded_int, bounded_float,
)
from pdf_generator import build_invoice_pdf
import theme

st.set_page_config(page_title="Invoice Generator", page_icon="🧾", layout="wide")
theme.inject(st)


# ---------------------------------------------------------------------------
# Optional access-code gate. Fully OFF unless you add [auth] access_code to
# .streamlit/secrets.toml -- keeps this safe to run locally with zero setup.
# ---------------------------------------------------------------------------
def _check_access_gate():
    try:
        required_code = st.secrets["auth"]["access_code"]
    except Exception:
        return True  # no gate configured

    if st.session_state.get("_authed"):
        return True

    st.title("🔒 Invoice Generator")
    code = st.text_input("Enter access code", type="password")
    if st.button("Unlock"):
        if code and code == required_code:
            st.session_state["_authed"] = True
            st.rerun()
        else:
            st.error("Incorrect code.")
    return False


if not _check_access_gate():
    st.stop()


st.title("🧾 Invoice Generator")
st.caption("Fill in the details below and generate a branded, downloadable PDF invoice.")

# ---------------------------------------------------------------------------
# 1. Company selection
# ---------------------------------------------------------------------------
st.header("1. Company (From)")

company_labels = {key: c["display_name"] for key, c in COMPANIES.items()}
company_key = st.selectbox(
    "Choose your company profile",
    options=list(company_labels.keys()),
    format_func=lambda k: company_labels[k],
)
company = dict(COMPANIES[company_key])  # shallow copy so edits don't mutate config

col_a, col_b = st.columns(2)
with col_a:
    company["legal_name"] = clean_text(st.text_input("Company legal name", value=company["legal_name"]))
    addr_text = st.text_area(
        "Company address (one line per row)",
        value="\n".join(company["address_lines"]), height=90,
    )
    company["address_lines"] = [clean_text(l) for l in addr_text.split("\n") if l.strip()]
    company["vat"] = clean_text(st.text_input("Company VAT number", value=company.get("vat", "")))
    company["cr"] = clean_text(st.text_input("Company CR number", value=company.get("cr", "")))
with col_b:
    company["contact"] = clean_text(st.text_input("Contact number(s)", value=company.get("contact", "")))
    company["email"] = clean_text(st.text_input("Email", value=company.get("email", "")))
    company["account_name"] = clean_text(st.text_input("Bank account name", value=company.get("account_name", "")))
    company["iban"] = clean_text(st.text_input("IBAN", value=company.get("iban", "")))

st.subheader("Logo & Stamp")
logo_col, stamp_col = st.columns(2)

logo_override_bytes = None
with logo_col:
    logo_choice = st.radio(
        "Logo", options=["Use company logo", CUSTOM_LOGO_LABEL],
        horizontal=True, key="logo_choice",
    )
    if logo_choice == CUSTOM_LOGO_LABEL:
        up = st.file_uploader("Upload logo (PNG/JPG, max 3MB)", type=["png", "jpg", "jpeg"], key="logo_up")
        if up is not None:
            try:
                logo_override_bytes = validate_uploaded_image(up)
                st.image(logo_override_bytes, width=180, caption="Logo preview")
            except ValidationError as e:
                st.error(str(e))
    else:
        st.image(company["logo_path"], width=180, caption="Company logo")

stamp_override_bytes = None
stamp_path_to_use = company["stamp_path"]
with stamp_col:
    stamp_choice = st.radio(
        "Stamp", options=["Use company stamp", CUSTOM_STAMP_LABEL, NO_STAMP_LABEL],
        horizontal=True, key="stamp_choice",
    )
    if stamp_choice == CUSTOM_STAMP_LABEL:
        up2 = st.file_uploader("Upload stamp (PNG/JPG, max 3MB)", type=["png", "jpg", "jpeg"], key="stamp_up")
        if up2 is not None:
            try:
                stamp_override_bytes = validate_uploaded_image(up2)
                st.image(stamp_override_bytes, width=140, caption="Stamp preview")
            except ValidationError as e:
                st.error(str(e))
        stamp_path_to_use = None
    elif stamp_choice == NO_STAMP_LABEL:
        stamp_path_to_use = None
    else:
        st.image(company["stamp_path"], width=140, caption="Company stamp")

company["stamp_path"] = stamp_path_to_use

st.divider()

# ---------------------------------------------------------------------------
# 2. Billed-to client
# ---------------------------------------------------------------------------
st.header("2. Billed To (Client)")

client_options = list(PRESET_CLIENTS.keys()) + [NEW_CLIENT_LABEL]
client_choice = st.selectbox("Choose a saved client or add a new one", options=client_options)

if client_choice == NEW_CLIENT_LABEL:
    default_client = {"name": "", "address_lines": [""], "cr": "", "vat": ""}
else:
    default_client = PRESET_CLIENTS[client_choice]

c1, c2 = st.columns(2)
with c1:
    bill_name = clean_text(st.text_input("Client name", value=default_client["name"]))
    bill_addr_text = st.text_area(
        "Client address (one line per row)",
        value="\n".join(default_client["address_lines"]), height=90,
    )
    bill_to_address = [clean_text(l) for l in bill_addr_text.split("\n") if l.strip()]
with c2:
    bill_cr = clean_text(st.text_input("Client CR number", value=default_client.get("cr", "")))
    bill_vat = clean_text(st.text_input("Client VAT number", value=default_client.get("vat", "")))

st.divider()

# ---------------------------------------------------------------------------
# 3. Invoice meta
# ---------------------------------------------------------------------------
st.header("3. Invoice Details")

m1, m2, m3, m4 = st.columns(4)
with m1:
    invoice_date = st.date_input("Date", value=datetime.date.today())
with m2:
    invoice_no = clean_text(st.text_input("Invoice No.", value=""))
with m3:
    lpo_no = clean_text(st.text_input("LPO No. (optional)", value=""))
with m4:
    payment_terms = clean_text(st.text_input("Payment Terms", value="ASAP"))

invoice_title = clean_text(
    st.text_input("Document title", value=company.get("invoice_title", "TAX INVOICE"))
)

st.divider()

# ---------------------------------------------------------------------------
# 4. Line items table
# ---------------------------------------------------------------------------
st.header("4. Items")

st.caption(
    "Add line items below. You can also add extra custom columns "
    f"(e.g. 'Remarks', 'Period') — up to {MAX_EXTRA_COLUMNS}. "
    "Unit Price × Qty, VAT and totals are calculated automatically."
)

extra_cols_text = st.text_input(
    "Extra custom column names (comma-separated, optional)",
    value="",
    help="Example: Remarks, Period",
)
extra_columns = []
if extra_cols_text.strip():
    for c in extra_cols_text.split(","):
        c = clean_text(c, 40)
        if c and c not in extra_columns:
            extra_columns.append(c)
    extra_columns = extra_columns[:MAX_EXTRA_COLUMNS]

if "n_rows" not in st.session_state:
    st.session_state.n_rows = 1

row_ctrl_col1, row_ctrl_col2, _ = st.columns([1, 1, 4])
with row_ctrl_col1:
    if st.button("➕ Add row") and st.session_state.n_rows < MAX_ITEM_ROWS:
        st.session_state.n_rows += 1
with row_ctrl_col2:
    if st.button("➖ Remove row") and st.session_state.n_rows > 1:
        st.session_state.n_rows -= 1

n_rows = bounded_int(st.session_state.n_rows, 1, MAX_ITEM_ROWS, 1)
st.session_state.n_rows = n_rows

items = []
for i in range(n_rows):
    with st.container(border=True):
        cols = st.columns([3] + [1.3] * len(extra_columns) + [1.2, 0.9, 1])
        desc = clean_text(
            cols[0].text_input(f"Description #{i+1}", key=f"desc_{i}",
                                placeholder="Charges for cleaning services for the month of ..."),
            300,
        )
        extra_vals = {}
        for j, col_name in enumerate(extra_columns):
            extra_vals[col_name] = clean_text(
                cols[1 + j].text_input(col_name, key=f"extra_{i}_{j}"), 120
            )
        unit_price = bounded_float(
            cols[1 + len(extra_columns)].number_input(
                "Unit Price", key=f"price_{i}", min_value=0.0, max_value=1_000_000.0,
                value=0.0, step=0.5, format="%.3f",
            ), 0.0, 1_000_000.0, 0.0,
        )
        qty = bounded_float(
            cols[2 + len(extra_columns)].number_input(
                "Qty", key=f"qty_{i}", min_value=0.0, max_value=100_000.0,
                value=1.0, step=1.0,
            ), 0.0, 100_000.0, 1.0,
        )
        vat_percent = bounded_float(
            cols[3 + len(extra_columns)].number_input(
                "VAT %", key=f"vat_{i}", min_value=0.0, max_value=100.0,
                value=DEFAULT_VAT_PERCENT, step=1.0,
            ), 0.0, 100.0, DEFAULT_VAT_PERCENT,
        )
        line_amount = unit_price * qty
        line_vat = line_amount * vat_percent / 100.0
        st.caption(f"Line total: **{line_amount + line_vat:,.3f} {CURRENCY}**  "
                   f"(Amount {line_amount:,.3f} + VAT {line_vat:,.3f})")

        items.append({
            "description": desc,
            "unit_price": unit_price,
            "qty": qty,
            "vat_percent": vat_percent,
            "extra": extra_vals,
        })

subtotal = sum(it["unit_price"] * it["qty"] for it in items)
total_vat = sum(it["unit_price"] * it["qty"] * it["vat_percent"] / 100.0 for it in items)
grand_total = subtotal + total_vat

st.markdown(
    f"### Subtotal: {subtotal:,.3f} {CURRENCY}  |  VAT: {total_vat:,.3f} {CURRENCY}  |  "
    f"**Grand Total: {grand_total:,.3f} {CURRENCY}**"
)

st.divider()

# ---------------------------------------------------------------------------
# 5. Payment details override + notes
# ---------------------------------------------------------------------------
st.header("5. Payment Details & Notes")
p1, p2 = st.columns(2)
with p1:
    account_name = clean_text(st.text_input("Account name on invoice", value=company["account_name"]))
    iban_val = clean_text(st.text_input("IBAN on invoice", value=company["iban"]))
with p2:
    notes = clean_multiline(
        st.text_area("Footer note", value="Please arrange payment at your earliest convenience.", height=80)
    )

st.divider()

# ---------------------------------------------------------------------------
# 6. Generate
# ---------------------------------------------------------------------------
st.header("6. Generate Invoice")

errors = []
if not bill_name:
    errors.append("Client name is required.")
if not invoice_no:
    errors.append("Invoice No. is required.")
if all(not it["description"] for it in items):
    errors.append("At least one line item needs a description.")

if errors:
    for e in errors:
        st.warning(e)

generate = st.button("📄 Generate PDF", type="primary", disabled=bool(errors))

if generate and not errors:
    invoice_data = {
        "company": company,
        "logo_override_bytes": logo_override_bytes,
        "stamp_override_bytes": stamp_override_bytes,
        "invoice_title": invoice_title,
        "invoice_no": invoice_no,
        "invoice_date": invoice_date.strftime("%d/%m/%Y"),
        "lpo_no": lpo_no,
        "payment_terms": payment_terms,
        "bill_to_name": bill_name,
        "bill_to_address": bill_to_address,
        "bill_to_cr": bill_cr,
        "bill_to_vat": bill_vat,
        "items": items,
        "extra_columns": extra_columns,
        "account_name": account_name,
        "iban": iban_val,
        "notes": notes,
    }
    try:
        with st.spinner("Building your PDF..."):
            pdf_bytes = build_invoice_pdf(invoice_data)
        st.success("Invoice generated!")
        fname = safe_filename(invoice_no, default="invoice") + ".pdf"
        st.download_button(
            "⬇️ Download PDF", data=pdf_bytes, file_name=fname, mime="application/pdf",
        )
        st.caption(f"File name: {fname}")
    except Exception as e:  # noqa: BLE001 - surface a clean message, log detail server-side
        st.error("Something went wrong while generating the PDF. Please check your inputs and try again.")
        st.exception(e)
