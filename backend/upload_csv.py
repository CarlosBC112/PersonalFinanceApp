# app/routes/upload_csv.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
from typing import Tuple, Dict, Any, List
from db import get_db
import models  # import your SQLAlchemy models (app.models)

router = APIRouter()

# Common column name candidates
DATE_COLS = ["date", "transaction date", "posted date", "transaction_date", "posted_date", "txn_date"]
DESC_COLS = ["description", "memo", "details", "transaction description", "merchant"]
AMOUNT_COLS = ["amount", "amt", "debit", "credit", "transaction amount", "money"]

def detect_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    header_lc = [c.lower().strip() for c in df.columns]
    date_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in DATE_COLS), None)
    desc_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in DESC_COLS), None)
    amount_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in AMOUNT_COLS), None)
    # fallback heuristics
    if date_col is None:
        # try any column that looks like a date in sample
        for c in df.columns:
            try:
                pd.to_datetime(df[c].dropna().iloc[:5])
                date_col = c
                break
            except Exception:
                continue
    if amount_col is None:
        # find numeric column with decimal or signs
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                amount_col = c
                break
    if desc_col is None:
        # fallback to first non-date, non-number column
        for c in df.columns:
            if c != date_col and c != amount_col:
                desc_col = c
                break
    return date_col, desc_col, amount_col

def normalize_amount(raw) -> Decimal:
    if pd.isna(raw):
        raise ValueError("empty amount")
    s = str(raw).strip()
    # remove currency symbols, parentheses and commas
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    s = s.replace("−", "-")
    try:
        return Decimal(s)
    except InvalidOperation:
        # maybe it's numeric already
        try:
            return Decimal(float(s))
        except Exception as e:
            raise ValueError(f"Could not parse amount: {raw}")

def normalize_date(raw) -> pd.Timestamp:
    if pd.isna(raw):
        raise ValueError("empty date")
    try:
        return pd.to_datetime(raw, infer_datetime_format=True, dayfirst=False)
    except Exception as e:
        # last resort: parse with pandas' to_datetime with errors='coerce'
        dt = pd.to_datetime(raw, errors='coerce')
        if pd.isna(dt):
            raise ValueError(f"Could not parse date: {raw}")
        return dt

def classify_with_rules(description: str) -> int:
    """
    Optional simple mapping: map description keywords to category_id.
    You may replace this with more advanced logic or AI fallback.
    """
    if not description:
        return None
    s = description.lower()
    mapping = {
        "amazon": "Social",
        "netflix": "Social",
        "starbucks": "Social",
        "whole foods": "Groceries",
        "trader joe": "Groceries",
        "shell": "Transportation",
        "exxon": "Transportation",
        "rent": "Housing",
        "mortgage": "Housing",
        "transfer to savings": "Savings",
        "paypal": "Social",
        "uber": "Transportation"
    }
    for k,v in mapping.items():
        if k in s:
            # find category id by name or return None
            cat = (Session.object_session if False else None)  # no-op placeholder
            # return actual category id by querying categories table at runtime if desired
            return None
    return None

@router.post("/upload/csv")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    customer_id: str = None   # in real app, derive from auth current_user
):
    # Basic validation
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    # Read bytes then pandas
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents), encoding='utf-8', dtype=str)
    except Exception:
        # try with common alternatives
        df = pd.read_csv(io.BytesIO(contents), encoding='latin1', dtype=str)

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty")

    # Detect columns
    date_col, desc_col, amount_col = detect_columns(df)
    if not date_col or not amount_col:
        raise HTTPException(status_code=400, detail="Could not detect date or amount columns in CSV")

    # Normalize and collect rows
    parsed_rows = []
    errors = []
    for idx, row in df.iterrows():
        raw_date = row.get(date_col)
        raw_desc = row.get(desc_col) if desc_col else ""
        raw_amount = row.get(amount_col)
        try:
            dt = normalize_date(raw_date).date()
            amt = normalize_amount(raw_amount)
            parsed_rows.append({
                "date": dt,
                "description": (str(raw_desc)[:500] if raw_desc is not None else ""),
                "amount": amt,
                "raw": row.to_dict()
            })
        except Exception as e:
            errors.append({"row_index": int(idx), "error": str(e)})

    # Insert into DB (transactional)
    inserted = 0
    if parsed_rows:
        try:
            for r in parsed_rows:
                tx = models.Transaction(
                    customer_id=customer_id or "unknown",  # in prod: get from auth
                    date_of_purchase=r["date"],
                    item_description=r["description"],
                    amount=r["amount"],
                    parsed_raw=str(r["raw"])
                )
                db.add(tx)
                inserted += 1
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")

    # Prepare immediate aggregates for response
    df_parsed = pd.DataFrame([{"date": r["date"], "description": r["description"], "amount": float(r["amount"])} for r in parsed_rows])
    total = float(df_parsed["amount"].sum()) if not df_parsed.empty else 0.0
    by_month = df_parsed.groupby(pd.to_datetime(df_parsed["date"]).dt.to_period("M"))["amount"].sum().reset_index().head(6).to_dict(orient="records")
    top_merchants = df_parsed.groupby("description")["amount"].sum().sort_values(ascending=False).head(5).reset_index().to_dict(orient="records")

    # Optionally: schedule a background job to update BI layer / regenerate extract
    # (implement `update_bi_extract` to publish `.hyper` or refresh Metabase)
    def update_bi_extract(customer_id_local: str):
        # placeholder - implement publishing logic here (Hyper API, REST publish, regenerate CSV for Metabase, etc.)
        # Example: export CSV snapshot for BI to read
        snapshot = df_parsed.copy()
        snapshot.to_csv(f"/tmp/finance_snapshot_{customer_id_local}.csv", index=False)

    background_tasks.add_task(update_bi_extract, customer_id or "unknown")

    return {
        "filename": file.filename,
        "parsed_count": len(parsed_rows),
        "inserted_count": inserted,
        "errors": errors,
        "total_amount": total,
        "last_6_months_by_month": by_month,
        "top_merchants": top_merchants,
        "sample_rows": parsed_rows[:5]
    }
