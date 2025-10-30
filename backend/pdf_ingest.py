# pdf_ingest.py
"""
PDF ingestion module tuned to Chase-like "Spending Report" PDFs.

Requirements:
    pip install pdfplumber pytesseract pillow python-dateutil
System:
    Install Tesseract binary for OCR (if you need OCR fallback).
"""

import re
import io
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pdfplumber
from PIL import Image
import pytesseract
import dateutil.parser as dparser

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\dexte\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# --- Configuration: known category headings in the PDF ---
# If your bank uses other category names, add them here.
KNOWN_CATEGORIES = {
    "BILLS_AND_UTILITIES",
    "EDUCATION",
    "ENTERTAINMENT",
    "FOOD_AND_DRINK",
    "GAS",
    "GROCERIES",
    "HOME",
    "PERSONAL",
    "PROFESSIONAL_SERVICES",
    "SHOPPING",
    "TRAVEL",
    # Add more if needed
}

# Regex patterns
# Date in the PDF is like "Feb 14, 2025" (month name, day, comma, year)
DATE_RE = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}'
# Amount like $14.99 or $-28.00 or -$28.00 or $1,234.56
AMOUNT_RE = r'(-?\$?\-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
# Full transaction line: often has two dates (Transaction Date and Posted Date),
# then description text, then amount at end.
TX_LINE_RE = re.compile(
    rf'^\s*({DATE_RE})\s+({DATE_RE})\s+(.+?)\s+{AMOUNT_RE}\s*$',
    flags=re.IGNORECASE
)

TOTAL_LINE_RE = re.compile(r'^\s*Total\s+\$?\-?\d', flags=re.IGNORECASE)
SPENDING_BY_CATEGORY_RE = re.compile(r'^Spending By Category', flags=re.IGNORECASE)

# --- Helpers ---


def _ocr_page_image(page) -> str:
    """Perform OCR on a pdfplumber page image; returns text."""
    try:
        # render page to PIL image at 300 dpi
        pil_img = page.to_image(resolution=300).original
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        buf.seek(0)
        img = Image.open(buf)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        # If OCR fails for some reason, return empty string
        print(f"OCR failed for page: {e}")
        return ""


def extract_text_from_pdf(path: str, use_ocr_fallback: bool = True) -> str:
    """Extracts text from a PDF. If a page has no selectable text and OCR fallback
    is enabled, will OCR that page."""
    pages_text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                pages_text.append(page_text)
            elif use_ocr_fallback:
                ocr_text = _ocr_page_image(page)
                pages_text.append(ocr_text)
            else:
                pages_text.append("")  # empty page
    return "\n".join(pages_text)


def normalize_amount(amount_str: str) -> Decimal:
    """Normalize amount string to Decimal (positive = expense by default in PDF).
    Handles formats like $14.99, -$28.00, $1,234.56, ($12.34)."""
    if not amount_str:
        return Decimal("0.00")
    s = amount_str.strip()
    # Remove currency symbols and parentheses
    s = s.replace("$", "").replace(",", "").strip()
    # Some PDFs have negative sign before or after
    # If in parentheses, interpret as negative
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    # normalize stray minus signs
    s = s.replace("−", "-")  # in case of Unicode minus
    try:
        return Decimal(s)
    except InvalidOperation:
        # fallback: try to remove any non-digit/.- characters
        s2 = re.sub(r'[^0-9\.-]', '', s)
        try:
            return Decimal(s2)
        except InvalidOperation:
            raise ValueError(f"Could not parse amount: {amount_str!r}")


def parse_transaction_line(line: str) -> Optional[Dict]:
    """Given a single line of text, try to parse a transaction row.
    Returns a dict with keys: tx_date (date), posted_date (date), description (str), amount (Decimal) or None.
    """
    m = TX_LINE_RE.match(line)
    if not m:
        return None
    tx_date_raw, posted_date_raw, desc_raw, amount_raw = m.group(1), m.group(2), m.group(3), m.group(4)
    try:
        tx_date = dparser.parse(tx_date_raw).date()
    except Exception:
        tx_date = None
    try:
        posted_date = dparser.parse(posted_date_raw).date()
    except Exception:
        posted_date = None
    try:
        amount = normalize_amount(amount_raw)
    except Exception:
        amount = None
    return {
        "transaction_date": tx_date,
        "posted_date": posted_date,
        "description": desc_raw.strip(),
        "amount": amount,
        "raw_line": line.strip()
    }


def split_into_sections(text: str) -> List[Tuple[Optional[str], List[str]]]:
    """
    Splits the big text into sections of (category_name, lines).
    Strategy:
      - Walk through lines.
      - When we hit an uppercase line matching a known category, start a new section.
      - If we encounter "Spending By Category" or repeated footer, stop capturing categories.
    Returns a list of tuples (category, lines). category may be None if unknown.
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    sections = []
    current_cat = None
    current_lines = []
    # We'll also attempt to detect heading lines that are exactly the category names
    for i, ln in enumerate(lines):
        ln_stripped = ln.strip()
        # Skip blank lines
        if not ln_stripped:
            continue
        # If line matches a known category heading exactly (or all-caps with underscores), switch
        if ln_stripped.upper() in KNOWN_CATEGORIES:
            # store previous section
            if current_lines:
                sections.append((current_cat, current_lines))
            current_cat = ln_stripped.upper()
            current_lines = []
            continue
        # Sometimes category appears followed by header "Transaction Date Posted Date Description Amount"
        # so skip that header line
        if re.match(r'^\s*Transaction Date', ln, flags=re.IGNORECASE):
            continue
        # If we hit "Spending By Category" stop parsing transaction sections (the rest is summary)
        if SPENDING_BY_CATEGORY_RE.search(ln):
            if current_lines:
                sections.append((current_cat, current_lines))
            break
        # Otherwise, append line
        current_lines.append(ln)
    # Append last section
    if current_lines:
        sections.append((current_cat, current_lines))
    return sections


def parse_transactions_from_text(text: str) -> List[Dict]:
    """
    High-level parse that returns a list of transaction dicts:
      {
        "category": str or None,
        "transaction_date": date or None,
        "posted_date": date or None,
        "description": str,
        "amount": Decimal,
        "raw_line": str
      }
    """
    results = []
    sections = split_into_sections(text)
    for cat, lines in sections:
        # lines holds many lines: transaction rows, totals, maybe page footers.
        for ln in lines:
            # Skip lines that are summary totals like "Total $269.98"
            if TOTAL_LINE_RE.match(ln):
                continue
            # Parse candidate transaction line
            tx = parse_transaction_line(ln)
            if tx:
                tx["category"] = cat
                results.append(tx)
            else:
                # Some transaction rows may be split across multiple PDF lines (description wrapped).
                # Heuristic: if previous line parsed and this line doesn't match, append to previous description.
                if results and ln.strip() and not re.match(r'^\d', ln.strip()):
                    # attach to last result's description (if it's likely a continuation)
                    last = results[-1]
                    # but only if the last raw_line has no trailing amount (i.e., continuation)
                    # We'll conservatively append.
                    last["description"] = (last.get("description", "") + " " + ln.strip()).strip()
                    last["raw_line"] = last["raw_line"] + " " + ln.strip()
                else:
                    # ignore other unrelated lines (headers, footers)
                    pass
    return results


# --- DB integration helper (example using SQLAlchemy models) ---
# Adapt the import lines to use your app.db Session and models.Transaction
def import_transactions_to_db(transactions: List[Dict], customer_id: str, db_session, models_module):
    """
    Sample insertion helper. Adapt to your models and session management.
    - transactions: list of dicts from parse_transactions_from_text
    - customer_id: str (UUID or PK for your customer table)
    - db_session: SQLAlchemy session
    - models_module: Python module where your SQLAlchemy models live (e.g. import app.models as models)
    """
    inserted = 0
    for tx in transactions:
        # dedupe check: optional - skip if a transaction with same date/amount/desc exists
        q = db_session.query(models_module.Transaction).filter(
            models_module.Transaction.customer_id == customer_id,
            models_module.Transaction.date_of_purchase == tx["transaction_date"],
            models_module.Transaction.amount == tx["amount"],
            models_module.Transaction.item_description.ilike(f'%{tx["description"][:50]}%')
        )
        if q.first():
            # already present; skip
            continue

        new = models_module.Transaction(
            customer_id=customer_id,
            date_of_purchase=tx["transaction_date"],
            item_description=tx["description"][:500],
            amount=tx["amount"],
            parsed_raw=tx["raw_line"],
            # category_id left null; you can map category names to IDs here if desired
            category_source='rule' if tx.get("category") else 'ai'
        )
        db_session.add(new)
        inserted += 1
    db_session.commit()
    return inserted


# --- Convenience high-level function ---
def ingest_pdf_file_to_transactions(path: str, use_ocr_fallback: bool = True) -> List[Dict]:
    """
    Extracts and parses transactions from a PDF path and returns list of transaction dicts.
    """
    text = extract_text_from_pdf(path, use_ocr_fallback=use_ocr_fallback)
    txs = parse_transactions_from_text(text)
    return txs


# --- Example usage ---
if __name__ == "__main__":
    import json
    sample_path = r"C:\Users\dexte\Downloads\Spending Report PDF.pdf"  # path to your PDF file
    # Extract and print raw text for debugging
    from pprint import pprint
    text = extract_text_from_pdf(sample_path, use_ocr_fallback=True)
    print("--- RAW EXTRACTED TEXT ---")
    print(text)
    print("--- END RAW TEXT ---\n")
    parsed = parse_transactions_from_text(text)
    print(f"Found {len(parsed)} transactions.")
    # print first 10 for inspection
    for t in parsed[:10]:
        # convert Decimal to string for JSON-friendly printing
        t_print = dict(t)
        t_print["amount"] = str(t_print["amount"]) if t_print.get("amount") is not None else None
        t_print["transaction_date"] = t_print["transaction_date"].isoformat() if t_print.get("transaction_date") else None
        t_print["posted_date"] = t_print["posted_date"].isoformat() if t_print.get("posted_date") else None
        print(json.dumps(t_print, indent=2))
