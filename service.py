from __future__ import annotations

import base64
import io
import re
from dataclasses import dataclass

from PIL import Image


MAX_QR_INPUT_LENGTH = 2048
SIZE_OPTIONS = {
    "small": 6,
    "medium": 10,
    "large": 14,
}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class QRCodeResult:
    data: bytes
    preview_src: str
    filename: str
    mimetype: str


@dataclass(frozen=True)
class BarcodeResult:
    data: bytes
    preview_src: str
    filename: str
    mimetype: str


def normalize_size(size: str | None) -> str:
    value = (size or "medium").strip().lower()
    return value if value in SIZE_OPTIONS else "medium"


def validate_payload(payload: str | None) -> str:
    value = (payload or "").strip()
    if not value:
        raise ValueError("Please enter text or a URL to generate a QR code.")
    if len(value) > MAX_QR_INPUT_LENGTH:
        raise ValueError(f"Input is too long. Maximum allowed length is {MAX_QR_INPUT_LENGTH} characters.")
    return value


def generate_qr_code(payload: str | None, size: str | None = "medium") -> QRCodeResult:
    value = validate_payload(payload)

    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("The QR code library is not installed. Please install qrcode[pil].") from exc

    size_key = normalize_size(size)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=SIZE_OPTIONS[size_key],
        border=4,
    )
    qr.add_data(value)
    qr.make(fit=True)

    image: Image.Image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    image_bytes = buffer.getvalue()
    preview = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}"

    return QRCodeResult(
        data=image_bytes,
        preview_src=preview,
        filename="atechabad-qr-code.png",
        mimetype="image/png",
    )


def generate_barcode(value: str | None, barcode_type: str | None = "code128") -> BarcodeResult:
    text = (value or "").strip()
    if not text:
        raise ValueError("Please enter a barcode value.")

    kind = (barcode_type or "code128").strip().lower()
    if kind not in {"code128", "ean13", "upca"}:
        kind = "code128"

    try:
        from barcode import get_barcode_class
        from barcode.writer import ImageWriter
    except ImportError as exc:
        raise RuntimeError("The barcode library is not installed. Please install python-barcode.") from exc

    if kind in {"ean13", "upca"} and not text.isdigit():
        raise ValueError("EAN-13 and UPC-A barcodes require numbers only.")
    if kind == "ean13" and len(text) not in {12, 13}:
        raise ValueError("EAN-13 requires 12 digits, or 13 digits including the check digit.")
    if kind == "upca" and len(text) not in {11, 12}:
        raise ValueError("UPC-A requires 11 digits, or 12 digits including the check digit.")

    barcode_class = get_barcode_class(kind)
    barcode = barcode_class(text, writer=ImageWriter())
    buffer = io.BytesIO()
    barcode.write(
        buffer,
        {
            "module_height": 14,
            "module_width": 0.28,
            "quiet_zone": 4,
            "font_size": 10,
            "text_distance": 4,
            "write_text": True,
        },
    )
    image_bytes = buffer.getvalue()
    preview = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}"

    return BarcodeResult(
        data=image_bytes,
        preview_src=preview,
        filename="atechabad-barcode.png",
        mimetype="image/png",
    )
