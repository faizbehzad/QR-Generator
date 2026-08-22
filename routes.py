from __future__ import annotations

import io
from urllib.parse import quote_plus

from flask import Blueprint, render_template, request, send_file

from QR_generator.service import generate_barcode, generate_qr_code, normalize_size


qr_generator_bp = Blueprint(
    "qr_generator",
    __name__,
    url_prefix="/qr-generator",
    static_folder="static",
    static_url_path="/static",
)


@qr_generator_bp.route("", methods=["GET", "POST"])
@qr_generator_bp.route("/", methods=["GET", "POST"])
def index():
    context = {
        "qr_text": "",
        "qr_mode": "url",
        "selected_size": "medium",
        "qr_preview": None,
        "barcode_text": "",
        "barcode_type": "code128",
        "barcode_preview": None,
        "form_values": {},
        "error": None,
        "barcode_error": None,
    }

    if request.method == "POST":
        action = request.form.get("action", "qr")
        context["form_values"] = request.form.to_dict()

        if action == "barcode":
            context["barcode_text"] = request.form.get("barcode_text", "").strip()
            context["barcode_type"] = request.form.get("barcode_type", "code128")

            try:
                result = generate_barcode(context["barcode_text"], context["barcode_type"])
                context["barcode_preview"] = result.preview_src
            except (RuntimeError, ValueError) as exc:
                context["barcode_error"] = str(exc)
        else:
            context["qr_text"] = build_qr_payload(request.form)
            context["qr_mode"] = request.form.get("qr_mode", "url")
            context["selected_size"] = normalize_size(request.form.get("size"))

            try:
                result = generate_qr_code(context["qr_text"], context["selected_size"])
                context["qr_preview"] = result.preview_src
            except (RuntimeError, ValueError) as exc:
                context["error"] = str(exc)

    return render_template("qr_generator.html", **context)


@qr_generator_bp.route("/download", methods=["POST"])
def download():
    result = generate_qr_code(request.form.get("qr_text"), request.form.get("size"))
    return send_file(
        io.BytesIO(result.data),
        mimetype=result.mimetype,
        as_attachment=True,
        download_name=result.filename,
    )


@qr_generator_bp.route("/barcode/download", methods=["POST"])
def barcode_download():
    result = generate_barcode(request.form.get("barcode_text"), request.form.get("barcode_type"))
    return send_file(
        io.BytesIO(result.data),
        mimetype=result.mimetype,
        as_attachment=True,
        download_name=result.filename,
    )


def build_qr_payload(form) -> str:
    mode = form.get("qr_mode", "url")

    if mode == "app":
        return form.get("app_url", "").strip()
    if mode == "text":
        return form.get("text_value", "").strip()
    if mode == "map":
        location = form.get("map_location", "").strip()
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(location)}" if location else ""
    if mode == "wifi":
        ssid = form.get("wifi_ssid", "").strip()
        password = form.get("wifi_password", "").strip()
        encryption = form.get("wifi_encryption", "WPA")
        hidden = "true" if form.get("wifi_hidden") else "false"
        return f"WIFI:T:{encryption};S:{ssid};P:{password};H:{hidden};;" if ssid else ""
    if mode == "audio":
        return form.get("audio_url", "").strip()
    if mode == "pdf":
        return form.get("pdf_url", "").strip()
    if mode == "whatsapp":
        phone = form.get("whatsapp_phone", "").strip().replace("+", "").replace(" ", "")
        message = form.get("whatsapp_message", "").strip()
        if not phone:
            return ""
        return f"https://wa.me/{phone}?text={quote_plus(message)}" if message else f"https://wa.me/{phone}"

    return form.get("url_value", "").strip()
