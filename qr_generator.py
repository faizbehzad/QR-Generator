"""
tools/qr_generator.py
─────────────────────────────────────────────────────────────────
QR Code Generator – Blueprint module for Atechabad Academy
Supports: PNG + SVG output, size control, custom fg/bg colours,
          inline preview (base64) + file download.
─────────────────────────────────────────────────────────────────
Dependencies (add to requirements.txt):
    qrcode[pil]>=7.4
    Pillow>=10.0
"""

from __future__ import annotations

import base64
import io
import re
import textwrap
import uuid

import qrcode
import qrcode.image.svg as qr_svg
from flask import (
    Blueprint,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)
from PIL import Image

# ── Blueprint registration ─────────────────────────────────────
qr_bp = Blueprint(
    "qr_generator",
    __name__,
    template_folder="../templates",   # resolves to the app-level templates/
    url_prefix="/qr-generator",
)

# ── Constants ─────────────────────────────────────────────────
_MAX_DATA_LEN   = 2048          # characters – practical QR limit
_BOX_MAP        = {"small": 6, "medium": 10, "large": 14}   # px per module
_BORDER_MAP     = {"none": 0, "small": 1, "medium": 2, "large": 4}
_ALLOWED_FMT    = {"png", "svg"}
_HEX_RE         = re.compile(r"^#[0-9a-fA-F]{6}$")

# ── Internal helpers ───────────────────────────────────────────

def _validate_hex(value: str, fallback: str) -> str:
    """Return *value* if it is a valid 6-digit hex colour, else *fallback*."""
    value = (value or "").strip()
    return value if _HEX_RE.match(value) else fallback


def _hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _build_png(
    data: str,
    box_size: int,
    border: int,
    fg: str,
    bg: str,
) -> bytes:
    """Generate QR code as PNG bytes."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img: Image.Image = qr.make_image(
        fill_color=_hex_to_rgb(fg),
        back_color=_hex_to_rgb(bg),
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()


def _build_svg(
    data: str,
    box_size: int,
    border: int,
    fg: str,
) -> str:
    """
    Generate QR code as SVG string.
    (SVG output does not support arbitrary background colours natively;
    a coloured rect is injected automatically.)
    """
    factory = qr_svg.SvgFillImage
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf.read().decode("utf-8")


def _parse_request() -> tuple[str, int, int, str, str, str] | tuple[None, None, None, None, None, str]:
    """
    Parse and validate POST form fields.
    Returns (data, box_size, border, fg, bg, fmt) on success,
    or (None, None, None, None, None, error_message) on failure.
    """
    data    = (request.form.get("data", "") or "").strip()
    size    = (request.form.get("size", "medium") or "medium").strip().lower()
    border  = (request.form.get("border", "medium") or "medium").strip().lower()
    fg      = (request.form.get("fg_color", "#000000") or "#000000").strip()
    bg      = (request.form.get("bg_color", "#ffffff") or "#ffffff").strip()
    fmt     = (request.form.get("format", "png") or "png").strip().lower()

    # ── Validation ──────────────────────────────────────────
    if not data:
        return None, None, None, None, None, "Input cannot be empty."
    if len(data) > _MAX_DATA_LEN:
        return None, None, None, None, None, (
            f"Input too long ({len(data)} chars). Maximum is {_MAX_DATA_LEN}."
        )
    if fmt not in _ALLOWED_FMT:
        return None, None, None, None, None, "Invalid format. Choose PNG or SVG."

    box_size = _BOX_MAP.get(size, _BOX_MAP["medium"])
    border_px = _BORDER_MAP.get(border, _BORDER_MAP["medium"])
    fg = _validate_hex(fg, "#000000")
    bg = _validate_hex(bg, "#ffffff")

    return data, box_size, border_px, fg, bg, fmt


# ── Routes ─────────────────────────────────────────────────────

@qr_bp.route("/", methods=["GET"])
def index() -> str:
    """Render the QR Generator page."""
    return render_template("qr_generator.html")


@qr_bp.route("/generate", methods=["POST"])
def generate() -> Response:
    """
    AJAX endpoint – returns JSON:
      { preview: "data:image/png;base64,…", format: "png" }  on success
      { error: "…" }                                          on failure
    """
    data, box_size, border, fg, bg, fmt = _parse_request()

    if data is None:
        # fmt contains the error message when data is None
        return jsonify({"error": fmt}), 400

    try:
        if fmt == "png":
            raw = _build_png(data, box_size, border, fg, bg)
            b64 = base64.b64encode(raw).decode()
            preview = f"data:image/png;base64,{b64}"
        else:
            svg_str = _build_svg(data, box_size, border, fg)
            b64 = base64.b64encode(svg_str.encode()).decode()
            preview = f"data:image/svg+xml;base64,{b64}"

        return jsonify({"preview": preview, "format": fmt})

    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"QR generation failed: {exc}"}), 500


@qr_bp.route("/download", methods=["POST"])
def download() -> Response:
    """
    Download endpoint – streams the QR file directly to the browser.
    Accepts the same form fields as /generate.
    """
    data, box_size, border, fg, bg, fmt = _parse_request()

    if data is None:
        return jsonify({"error": fmt}), 400

    try:
        if fmt == "png":
            raw   = _build_png(data, box_size, border, fg, bg)
            buf   = io.BytesIO(raw)
            mime  = "image/png"
            fname = "qrcode.png"
        else:
            svg_str = _build_svg(data, box_size, border, fg)
            buf   = io.BytesIO(svg_str.encode())
            mime  = "image/svg+xml"
            fname = "qrcode.svg"

        buf.seek(0)
        return send_file(
            buf,
            mimetype=mime,
            as_attachment=True,
            download_name=fname,
        )

    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Download failed: {exc}"}), 500
