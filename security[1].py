"""
security.py
------------
Small set of defensive helpers used everywhere user input touches the
app: text going into the PDF, uploaded image files, and generated file
names.

Design goals
- Never trust text before it reaches ReportLab (which interprets a
  mini-XML markup inside Paragraph text) -> always escape.
- Never trust an uploaded file's extension -> re-verify with Pillow that
  the bytes really decode as an image, re-encode it ourselves, and cap
  its size and pixel dimensions (guards against decompression-bomb style
  files).
- Never build filesystem paths directly from user text -> always run
  file names through safe_filename() and keep everything inside a
  dedicated temp directory.
- Keep numeric inputs bounded so a typo/malicious value can't produce a
  pathological PDF (e.g. a million-row table).
"""

import io
import re
import uuid

from xml.sax.saxutils import escape
from PIL import Image, UnidentifiedImageError

from config import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, MAX_TEXT_LEN, MAX_MULTILINE_LEN

# Reasonable ceiling on pixel dimensions to guard against decompression bombs
MAX_IMAGE_PIXELS = 4000 * 4000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class ValidationError(Exception):
    """Raised when user-supplied input fails a security/sanity check."""


def clean_text(value: str, max_len: int = MAX_TEXT_LEN) -> str:
    """
    Trim, cap length, and strip control/non-printable characters from a
    single-line text field. Does NOT escape XML here -- escaping happens
    right before the value is placed into a ReportLab Paragraph, so the
    same clean value can still be shown as plain text in Streamlit.
    """
    if value is None:
        return ""
    value = str(value)
    value = value.strip()
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)  # control chars
    if len(value) > max_len:
        value = value[:max_len]
    return value


def clean_multiline(value: str, max_len: int = MAX_MULTILINE_LEN) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    if len(value) > max_len:
        value = value[:max_len]
    return value


def xml_safe(value: str) -> str:
    """Escape a cleaned string so it is safe to embed in a ReportLab Paragraph."""
    return escape(clean_text(value, MAX_MULTILINE_LEN))


def safe_filename(value: str, default: str = "invoice") -> str:
    """
    Produce a filesystem-safe file name (no path separators, no traversal,
    letters/digits/dash/underscore only), falling back to a random name
    if the input is empty after sanitizing.
    """
    value = clean_text(value or "", 100)
    value = re.sub(r"[^A-Za-z0-9_\-]+", "_", value).strip("_")
    if not value:
        value = default
    return f"{value}_{uuid.uuid4().hex[:8]}"


def validate_uploaded_image(uploaded_file) -> bytes:
    """
    Validate a Streamlit UploadedFile that is supposed to be a logo/stamp
    image. Returns re-encoded PNG bytes on success, or raises
    ValidationError with a user-facing message on failure.

    Checks performed:
      1. Extension is in the allow-list.
      2. Size is under MAX_UPLOAD_BYTES (checked before fully decoding).
      3. Pillow can actually decode it as an image (rejects renamed
         non-image files, e.g. a script with a .png extension).
      4. Pixel dimensions are bounded (decompression-bomb guard, also
         enforced globally via Image.MAX_IMAGE_PIXELS).
      5. The image is re-saved through Pillow as a clean PNG, which
         strips any embedded scripts/metadata/polyglot payloads instead
         of passing the original bytes through untouched.
    """
    if uploaded_file is None:
        raise ValidationError("No file provided.")

    name = getattr(uploaded_file, "name", "") or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. Please upload a PNG or JPG image."
        )

    raw = uploaded_file.getvalue()
    if not raw:
        raise ValidationError("The uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"File is too large. Please keep uploads under {MAX_UPLOAD_BYTES // (1024*1024)} MB."
        )

    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()  # cheap structural check
        # re-open after verify() (verify() leaves the file unusable for further ops)
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("This file doesn't look like a valid image.")

    if img.width * img.height > MAX_IMAGE_PIXELS:
        raise ValidationError("Image resolution is too large.")

    # Normalize to RGB/RGBA and re-encode -> strips any non-pixel payload
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def bounded_int(value, low: int, high: int, default: int) -> int:
    """Clamp a numeric UI input into [low, high], falling back to default on bad input."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def bounded_float(value, low: float, high: float, default: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if value != value:  # NaN check
        return default
    return max(low, min(high, value))
