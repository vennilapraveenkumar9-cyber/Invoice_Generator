"""
pdf_generator.py
-----------------
Builds the final invoice PDF with ReportLab (Platypus) from a plain-dict
"invoice data" structure assembled by app.py. Kept independent of
Streamlit so it can be unit-tested or reused from a CLI/script.

All free-text fields are escaped with security.xml_safe() right before
they are placed into a Paragraph, since ReportLab Paragraph text is
interpreted as a small XML/HTML-like markup language.
"""

import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
)
from reportlab.platypus.flowables import HRFlowable

from security import xml_safe
from wordify import amount_to_words
from config import PAGE_BACKGROUND_COLOR

CURRENCY = "BHD"

# Target print resolution for embedded logo/stamp/banner images. Source
# scans are often lower-res than this; we resample up to it with a
# high-quality filter + unsharp mask (see _enhance_clarity) so edges look
# crisp in the PDF instead of soft/blurry when stretched to size.
TARGET_DPI = 300


def _style_sheet():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CompanyName", fontName="Helvetica-Bold", fontSize=16, leading=19,
    ))
    styles.add(ParagraphStyle(
        name="InvoiceTitle", fontName="Helvetica-Bold", fontSize=15, leading=18,
        alignment=TA_CENTER, spaceBefore=6, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SmallRight", parent=styles["Normal"], fontSize=8.5, leading=11,
        alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="CellHeader", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9.5, leading=12,
    ))
    styles.add(ParagraphStyle(
        name="Cell", parent=styles["Normal"], fontSize=9.5, leading=12,
    ))
    styles.add(ParagraphStyle(
        name="CellRight", parent=styles["Cell"], alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="CellCenter", parent=styles["Cell"], alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="BoldCell", parent=styles["Cell"], fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="Small", parent=styles["Normal"], fontSize=9, leading=12,
    ))
    styles.add(ParagraphStyle(
        name="Footer", parent=styles["Normal"], fontSize=8, leading=10,
        textColor=colors.white, alignment=TA_CENTER,
    ))
    return styles


def _enhance_clarity(pil_img, target_px_w, target_px_h):
    """
    Improve the *perceived* sharpness/clarity of a logo/stamp image before
    it's embedded in the PDF.

    Scanned letterhead crops tend to look soft once stretched to fill a
    wide banner. We can't invent detail that isn't in the source, but we
    can:
      1. Resize with LANCZOS (a high-quality resampling filter) to the
         exact pixel size the PDF will actually display it at, instead of
         letting the PDF viewer do a cheap scale -- this alone removes a
         lot of the "blurry stretch" look.
      2. Apply a mild autocontrast pass to punch up washed-out scan
         contrast (common with these scanned invoices).
      3. Apply an UnsharpMask to recover crisp edges after resizing.
    """
    from PIL import Image as PILImage, ImageOps, ImageFilter

    target_px_w = max(1, int(target_px_w))
    target_px_h = max(1, int(target_px_h))

    resized = pil_img.resize((target_px_w, target_px_h), resample=PILImage.LANCZOS)

    # autocontrast needs an alpha-free image to work on cleanly; reapply
    # the original alpha channel afterwards if present.
    if resized.mode == "RGBA":
        rgb = resized.convert("RGB")
        alpha = resized.split()[-1]
        rgb = ImageOps.autocontrast(rgb, cutoff=1)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.6, percent=140, threshold=3))
        resized = rgb.convert("RGBA")
        resized.putalpha(alpha)
    else:
        resized = ImageOps.autocontrast(resized.convert("RGB"), cutoff=1)
        resized = resized.filter(ImageFilter.UnsharpMask(radius=1.6, percent=140, threshold=3))

    return resized


def _safe_image(path_or_bytes, max_w, max_h, align="LEFT", stretch_width=False):
    """
    Load an image (path or raw bytes), sharpen/clean it up, and scale it
    to fit within a box.

    stretch_width=False (default): fit within (max_w, max_h) preserving
        aspect ratio -- used for the YSCC-style logo and the stamp, so
        they're never distorted.
    stretch_width=True: always fill the full max_w edge-to-edge (height
        follows the image's own aspect ratio) -- used for the full-page
        letterhead banner so it visually spans the page like the samples,
        instead of floating with side margins if its aspect ratio happens
        to be wider than max_h allows.

    Returns None if the image can't be loaded.
    """
    if not path_or_bytes:
        return None
    try:
        from PIL import Image as PILImage
        if isinstance(path_or_bytes, (bytes, bytearray)):
            buf = io.BytesIO(path_or_bytes)
            pil_img = PILImage.open(buf)
        else:
            if not os.path.isfile(path_or_bytes):
                return None
            pil_img = PILImage.open(path_or_bytes)
        pil_img = pil_img.convert("RGBA")
        w, h = pil_img.size

        if stretch_width:
            scale = max_w / w
            # Safety net: if stretching to full width would make an
            # unusually tall/portrait image absurdly high (e.g. someone
            # uploads the wrong file), fall back to a generous height cap
            # instead of blowing out the page layout.
            hard_cap_h = max_h * 1.6
            if h * scale > hard_cap_h:
                scale = hard_cap_h / h
        else:
            scale = min(max_w / w, max_h / h)
        disp_w, disp_h = w * scale, h * scale

        # Render at ~300 DPI worth of pixels for the final display size
        # (rather than dumping the original, possibly-lower-res pixels
        # straight into the PDF) so edges stay crisp instead of blurry
        # when stretched across a wide banner.
        target_px_w = disp_w / mm * (300 / 25.4)
        target_px_h = disp_h / mm * (300 / 25.4)
        pil_img = _enhance_clarity(pil_img, target_px_w, target_px_h)

        buf2 = io.BytesIO()
        pil_img.save(buf2, format="PNG")
        buf2.seek(0)
        img_flowable = RLImage(buf2, width=disp_w, height=disp_h)
        # ReportLab's Image flowable defaults to CENTER alignment inside its
        # available width. For the standard header/stamp we want it flush
        # LEFT (under "Authorized Signatory & Stamp" and in the header);
        # for a full-width banner logo we explicitly want CENTER instead.
        img_flowable.hAlign = align
        return img_flowable
    except Exception:
        return None


def build_invoice_pdf(data: dict) -> bytes:
    """
    data keys expected:
      company: dict (see config.COMPANIES entries) with resolved logo/stamp
               as either a filesystem path (str) or raw bytes under
               'logo_bytes' / 'stamp_bytes' (uploaded overrides win).
      invoice_title, invoice_no, invoice_date, lpo_no, payment_terms
      bill_to_name, bill_to_address (list[str]), bill_to_cr, bill_to_vat
      items: list of dicts: description, unit_price, qty, vat_percent,
             extra: dict(col_name -> value)
      extra_columns: list[str] (custom column names, in order)
      account_name, iban, bank_note
      notes (optional free text)
    Returns: PDF bytes
    """
    styles = _style_sheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title=xml_safe(data.get("invoice_no", "Invoice")),
    )

    company = data["company"]
    story = []

    # ---------------------------------------------------------- header ----
    header_style = company.get("header_style", "standard")
    content_width = doc.width  # full usable width between margins

    if header_style == "banner":
        # The company supplied a single "full top part" image that already
        # contains the logo, wordmark, and contact details -- so it's shown
        # centered, spanning the page width, with no separate contact block
        # underneath (that info is already inside the image).
        banner_flowable = _safe_image(
            data.get("logo_override_bytes") or company.get("logo_path"),
            max_w=content_width, max_h=42 * mm, align="CENTER", stretch_width=True,
        )
        if banner_flowable:
            story.append(banner_flowable)
        story.append(Spacer(1, 6))
    else:
        logo_flowable = _safe_image(
            data.get("logo_override_bytes") or company.get("logo_path"),
            max_w=70 * mm, max_h=28 * mm, align="LEFT",
        )
        contact_lines = []
        if company.get("contact"):
            contact_lines.append(f"Contact: {xml_safe(company['contact'])}")
        if company.get("email"):
            contact_lines.append(f"Email: {xml_safe(company['email'])}")
        if company.get("cr"):
            contact_lines.append(f"CR: {xml_safe(company['cr'])}")
        contact_para = Paragraph("<br/>".join(contact_lines), styles["SmallRight"])

        header_table = Table(
            [[logo_flowable or "", contact_para]],
            colWidths=[100 * mm, None],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#999999")))
    story.append(Spacer(1, 8))

    story.append(Paragraph(xml_safe(data.get("invoice_title") or company.get("invoice_title", "TAX INVOICE")),
                            styles["InvoiceTitle"]))

    # -------------------------------------------------- meta info table ---
    meta_rows = [
        ["Date:", xml_safe(data.get("invoice_date", ""))],
        ["Invoice No.:", xml_safe(data.get("invoice_no", ""))],
        ["LPO No.:", xml_safe(data.get("lpo_no", "") or "--------")],
        ["Payment Terms:", xml_safe(data.get("payment_terms", "ASAP"))],
    ]
    meta_table = Table(
        [[Paragraph(f"<b>{r[0]}</b>", styles["Cell"]), Paragraph(r[1], styles["Cell"])] for r in meta_rows],
        colWidths=[45 * mm, None],
    )
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # --------------------------------------------------- billed-to / from -
    bill_addr = "<br/>".join(xml_safe(l) for l in data.get("bill_to_address", []) if l)
    from_addr = "<br/>".join(xml_safe(l) for l in company.get("address_lines", []) if l)

    bill_bottom = bill_addr
    if data.get("bill_to_cr"):
        bill_bottom += f"<br/>CR: {xml_safe(data['bill_to_cr'])}"
    if data.get("bill_to_vat"):
        bill_bottom += f"<br/>VAT: {xml_safe(data['bill_to_vat'])}"

    from_bottom = from_addr
    if company.get("vat"):
        from_bottom += f"<br/>VAT: {xml_safe(company['vat'])}"

    divider_color = colors.HexColor("#9AA3AF")

    bill_cell = [
        Paragraph(f"<b>Billed To:</b><br/><b>{xml_safe(data.get('bill_to_name',''))}</b>", styles["Cell"]),
        HRFlowable(width="100%", thickness=0.6, color=divider_color, spaceBefore=4, spaceAfter=4),
        Paragraph(bill_bottom, styles["Cell"]),
    ]
    from_cell = [
        Paragraph(f"<b>From:</b><br/><b>{xml_safe(company.get('legal_name',''))}</b>", styles["Cell"]),
        HRFlowable(width="100%", thickness=0.6, color=divider_color, spaceBefore=4, spaceAfter=4),
        Paragraph(from_bottom, styles["Cell"]),
    ]

    parties_table = Table(
        [[bill_cell, from_cell]],
        colWidths=[None, None],
    )
    parties_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 8))

    # ------------------------------------------------------- items table --
    extra_columns = data.get("extra_columns", [])
    has_vat_column = any(item.get("vat_percent", 0) not in (None, "") for item in data["items"])

    header = ["S.No", "Description"] + extra_columns + ["Unit Price", "Qty"]
    if has_vat_column:
        header += ["VAT %", "VAT Amt"]
    header += ["Total"]
    header_row = [Paragraph(h, styles["CellHeader"]) for h in header]

    rows = [header_row]
    subtotal = 0.0
    total_vat = 0.0

    for idx, item in enumerate(data["items"], start=1):
        desc = xml_safe(item.get("description", ""))
        unit_price = float(item.get("unit_price", 0) or 0)
        qty_raw = item.get("qty", 1)
        try:
            qty_num = float(qty_raw)
            qty_display = f"{qty_num:g}"
        except (TypeError, ValueError):
            qty_num = 1.0
            qty_display = xml_safe(str(qty_raw) or "1")
        vat_percent = item.get("vat_percent", 0) or 0
        try:
            vat_percent = float(vat_percent)
        except (TypeError, ValueError):
            vat_percent = 0.0

        line_amount = unit_price * qty_num
        line_vat = line_amount * vat_percent / 100.0
        line_total = line_amount + line_vat

        subtotal += line_amount
        total_vat += line_vat

        row = [
            Paragraph(str(idx), styles["Cell"]),
            Paragraph(desc, styles["Cell"]),
        ]
        for col in extra_columns:
            row.append(Paragraph(xml_safe(item.get("extra", {}).get(col, "")), styles["Cell"]))
        row.append(Paragraph(f"{unit_price:,.3f}", styles["CellRight"]))
        row.append(Paragraph(qty_display, styles["CellCenter"]))
        if has_vat_column:
            row.append(Paragraph(f"{vat_percent:g}%", styles["CellCenter"]))
            row.append(Paragraph(f"{line_vat:,.3f}", styles["CellRight"]))
        row.append(Paragraph(f"{line_total:,.3f}", styles["CellRight"]))
        rows.append(row)

    grand_total = subtotal + total_vat

    # totals row
    n_cols = len(header)
    totals_label_span = n_cols - (2 if has_vat_column else 1) - 1
    totals_row = [""] * n_cols
    totals_row[0] = Paragraph("<b>Total</b>", styles["BoldCell"])
    if has_vat_column:
        totals_row[-2] = Paragraph(f"<b>{total_vat:,.3f}</b>", styles["CellRight"])
    totals_row[-1] = Paragraph(f"<b>{grand_total:,.3f}</b>", styles["CellRight"])
    rows.append(totals_row)

    n_extra = len(extra_columns)
    col_widths = [12 * mm, None] + [22 * mm] * n_extra + [24 * mm, 14 * mm]
    if has_vat_column:
        col_widths += [16 * mm, 20 * mm]
    col_widths += [24 * mm]

    items_table = Table(rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -2), 0.6, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, -1), (totals_label_span, -1)),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8))

    # ------------------------------------------------------------ totals -
    story.append(Paragraph(f"<b>Total: {grand_total:,.3f} {CURRENCY}</b>", styles["Small"]))
    story.append(Paragraph(f"Amount in Words: {xml_safe(amount_to_words(grand_total, CURRENCY))}",
                            styles["Small"]))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------- payment ----
    story.append(Paragraph("<b>Payment Details:</b>", styles["Small"]))
    story.append(Paragraph(
        f"Account Name: <b>{xml_safe(data.get('account_name', company.get('account_name','')))}</b>",
        styles["Small"]))
    story.append(Paragraph(
        f"IBAN: <b>{xml_safe(data.get('iban', company.get('iban','')))}</b>",
        styles["Small"]))
    story.append(Spacer(1, 8))

    if data.get("notes"):
        story.append(Paragraph(xml_safe(data["notes"]), styles["Small"]))
        story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Please arrange payment at your earliest convenience.", styles["Small"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Authorized Signatory &amp; Stamp</b>", styles["Small"]))
    story.append(Spacer(1, 6))

    stamp_flowable = _safe_image(
        data.get("stamp_override_bytes") or company.get("stamp_path"),
        max_w=42 * mm, max_h=42 * mm, align="LEFT",
    )
    if stamp_flowable:
        story.append(stamp_flowable)

    def _page_decorations(canvas, doc_):
        page_w, page_h = doc_.pagesize
        canvas.saveState()

        # ---- paper background (matches the sampled tone of the original
        # scanned invoices, instead of ReportLab's default stark white) ----
        canvas.setFillColor(colors.HexColor(PAGE_BACKGROUND_COLOR))
        canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        canvas.restoreState()

        # ---- footer band (only for companies whose sample has one) ----
        tagline = company.get("footer_tagline")
        if tagline:
            canvas.saveState()
            band_h = 8 * mm
            bg = company.get("footer_bg_color") or company.get("brand_color", "#1F3864")
            fg = company.get("footer_text_color", "#FFFFFF")
            accent = company.get("footer_accent_color")

            canvas.setFillColor(colors.HexColor(bg))
            canvas.rect(0, 0, page_w, band_h, stroke=0, fill=1)

            if accent:
                accent_w = 14 * mm
                canvas.setFillColor(colors.HexColor(accent))
                canvas.rect(page_w - accent_w, 0, accent_w, band_h, stroke=0, fill=1)

            canvas.setFillColor(colors.HexColor(fg))
            canvas.setFont("Helvetica", 7.5)
            canvas.drawCentredString(page_w / 2.0, band_h / 2.0 - 2.5, tagline[:180])
            canvas.restoreState()

    doc.build(story, onFirstPage=_page_decorations, onLaterPages=_page_decorations)
    return buf.getvalue()
