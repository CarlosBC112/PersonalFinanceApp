# pdf_parser.py
import pdfplumber
import re

def extract_text_from_pdf(path):
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return "\n".join(texts)

def parse_transactions_from_text(text):
    """
    Very simple heuristic: search for lines that look like 'MM/DD/YYYY  DESCRIPTION  $AMOUNT'
    You'll need to adapt/or write per-bank parsers.
    """
    lines = text.splitlines()
    txs = []
    date_re = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
    amount_re = re.compile(r'(-?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
    for line in lines:
        if date_re.search(line) and amount_re.search(line):
            txs.append(line.strip())
    return txs
