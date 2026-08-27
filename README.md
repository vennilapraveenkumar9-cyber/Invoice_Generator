# Invoice Generator (Streamlit)

A configurable invoice generator built for your company's invoicing needs.
Pick a company profile, pick or type a client address, build a line-item
table with automatic VAT/total calculation, and download a polished PDF —
styled to match your existing tax invoices.

## Features

- **3 company profiles** (logo, stamp, address, VAT/CR, bank details) —
  all fields editable per-invoice, or upload your own logo/stamp on the fly.
- **Saved client addresses** with one-click autofill, or add a brand-new
  client address any time.
- **Dynamic item table** — add/remove rows, add custom extra columns
  (e.g. "Remarks", "Period"), automatic Amount / VAT / Total calculation
  and amount-in-words.
- **One-click PDF download**, generated entirely in memory.
- **Security-hardened**: input length limits, XML-escaping before PDF
  generation, strict image-upload validation (type/size/real-image
  check, re-encoded through Pillow), bounded numeric/row limits, optional
  password gate.

## Project structure

```
invoice_app/
├── app.py               # Streamlit UI
├── pdf_generator.py      # ReportLab PDF building
├── config.py             # Company profiles & preset clients (edit me!)
├── security.py           # Input sanitization / upload validation
├── wordify.py             # Amount-to-words helper
├── requirements.txt
├── assets/
│   ├── logos/{yscc,aljameel,whiteness}.png
│   └── stamps/{yscc,aljameel,whiteness}.png
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Deploy on Streamlit Community Cloud

1. Push this folder to a **new GitHub repository**.
2. Go to https://share.streamlit.io → "New app".
3. Select your repo, branch, and set the main file to `app.py`.
4. Click **Deploy**.

That's it — `requirements.txt` is picked up automatically.

## Customizing companies / clients

Open `config.py`:

- `COMPANIES` — add/edit entries. Each needs a `logo_path` and
  `stamp_path` pointing at a PNG/JPG inside `assets/`. Drop your real
  logo/stamp files into `assets/logos/` and `assets/stamps/` and update
  the paths (or just replace the existing PNGs — same filenames).
- `PRESET_CLIENTS` — add/edit saved "Billed To" addresses.

No code changes are needed anywhere else — the UI reads directly from
this file.

## Optional: password-protect the app

By default the app has **no login** — anyone with the URL can use it.
If you're deploying somewhere semi-public and want a simple shared
password:

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   (locally) and set a real `access_code`.
2. On Streamlit Cloud, instead paste the same content into your app's
   **Settings → Secrets**.
3. Redeploy/restart. Visitors will now see a code prompt before the app.

`secrets.toml` is already git-ignored — never commit real secrets.

## Notes on the bundled logos/stamps

The logo and stamp images bundled under `assets/` were cropped from the
sample invoices you provided, so they may look slightly soft/scanned.
Swap in your original high-resolution logo/stamp files (same filenames,
PNG or JPG) for a crisper result — no code changes required.

## Security summary

- Every text field is length-capped and stripped of control characters
  before use, and XML-escaped right before being placed into the PDF
  (ReportLab's `Paragraph` interprets a small XML-like markup language,
  so this prevents both broken layout and markup injection).
- Uploaded images are checked for allowed extension, capped file size,
  verified as genuine image data with Pillow (`Image.verify()` +
  reload), capped in pixel dimensions (decompression-bomb guard), and
  **re-encoded** as clean PNGs before use — the original uploaded bytes
  are never persisted or passed through untouched.
- Row counts, VAT percentages, prices and quantities are all clamped to
  sane numeric ranges.
- Generated PDFs are built fully in-memory (`io.BytesIO`) — nothing is
  written to a guessable path on disk.
- Downloaded file names are sanitized (`security.safe_filename`) and
  suffixed with a random id — no path traversal from user-entered
  invoice numbers.
- An optional shared-password gate is available via `st.secrets` (off
  by default).

If you deploy this publicly and expect sensitive client data, also
consider: enabling the access-code gate, restricting the Streamlit Cloud
app visibility, and periodically rotating the access code.
