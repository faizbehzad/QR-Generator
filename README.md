# QR Code & Barcode Generator

A lightweight Flask web tool for generating QR codes and barcodes with instant previews and PNG downloads.

## Features

- Generate QR codes for URLs, text, maps, Wi-Fi, WhatsApp, PDFs, audio, and app links
- Generate Code 128, EAN-13, and UPC-A barcodes
- Choose QR output size
- Instant in-browser previews
- Download generated QR codes and barcodes as PNG files
- Input validation for empty and oversized payloads
- Responsive web interface

## Tech Stack

- Python
- Flask
- HTML/CSS/JavaScript
- `qrcode[pil]`
- `python-barcode`
- Pillow

## Project Structure

```text
QR-Generator/
├── app.py
├── routes.py
├── service.py
├── __init__.py
├── qr_generator.html
├── requirements.txt
├── templates/
├── static/
└── .gitignore
```

## Run Locally

1. Clone the repository:

```bash
git clone https://github.com/faizbehzad/QR-Generator.git
cd QR-Generator
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the Flask app:

```bash
python app.py
```

5. Open the local address shown by Flask in your browser.

## Notes

The QR generator validates payload length and supports high error correction. Barcode generation validates numeric requirements for EAN-13 and UPC-A formats.

## Author

**Faiz Behzad**  
GitHub: https://github.com/faizbehzad
