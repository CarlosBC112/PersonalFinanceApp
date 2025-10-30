# PersonalFinanceApp

## Dependencies

### Python Packages
- pdfplumber
- pytesseract
- pillow
- python-dateutil

Install all Python dependencies with:
```
pip install -r requirements.txt
```

### System Requirements
- Tesseract OCR
  - Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
  - Add the Tesseract installation directory to your system PATH (e.g., `C:\Users\<username>\AppData\Local\Programs\Tesseract-OCR`)

## Setup
1. Create and activate a Python virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR and ensure the path is configured in your code if not installed in the default location.

## Usage
Run the PDF ingestion script:
```
python backend/pdf_ingest.py
```

Make sure your PDF file path is set correctly in the script.
