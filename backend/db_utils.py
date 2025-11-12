from Database import engine, SessionLocal
from models import Base, Transaction
from decimal import Decimal, InvalidOperation
import pandas as pd
from typing import List, Dict


def create_tables():
    """Create tables defined in models.py on the configured engine."""
    Base.metadata.create_all(bind=engine)


def detect_columns(df: pd.DataFrame):
    header_lc = [c.lower().strip() for c in df.columns]
    date_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in ["date","transaction date","posted date","transaction_date","posted_date","txn_date"]), None)
    desc_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in ["description","memo","details","transaction description","merchant"]), None)
    amount_col = next((df.columns[i] for i,c in enumerate(header_lc) if c in ["amount","amt","debit","credit","transaction amount","money"]), None)
    # fallback
    if date_col is None:
        for c in df.columns:
            try:
                pd.to_datetime(df[c].dropna().iloc[:5])
                date_col = c
                break
            except Exception:
                continue
    if amount_col is None:
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                amount_col = c
                break
    if desc_col is None:
        for c in df.columns:
            if c != date_col and c != amount_col:
                desc_col = c
                break
    return date_col, desc_col, amount_col


def normalize_amount(raw) -> Decimal:
    if pd.isna(raw):
        raise ValueError("empty amount")
    s = str(raw).strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    s = s.replace("−", "-")
    try:
        return Decimal(s)
    except InvalidOperation:
        try:
            return Decimal(float(s))
        except Exception:
            raise ValueError(f"Could not parse amount: {raw}")


def insert_df_transactions(df: pd.DataFrame, customer_id: str = "unknown") -> Dict:
    """Insert parsed transactions from DataFrame into DB.

    Returns a dict with inserted_count and errors list.
    """
    date_col, desc_col, amount_col = detect_columns(df)
    if not date_col or not amount_col:
        return {"inserted": 0, "errors": ["Could not detect date or amount columns"]}

    session = SessionLocal()
    inserted = 0
    errors: List[Dict] = []
    objs = []
    for idx, row in df.iterrows():
        raw_date = row.get(date_col)
        raw_desc = row.get(desc_col) if desc_col else ""
        raw_amount = row.get(amount_col)
        try:
            dt = pd.to_datetime(raw_date, errors='raise').date()
            amt = normalize_amount(raw_amount)
            tx = Transaction(
                customer_id=customer_id,
                date_of_purchase=dt,
                item_description=(str(raw_desc)[:500] if raw_desc is not None else ""),
                amount=amt,
                parsed_raw=str(row.to_dict())
            )
            objs.append(tx)
        except Exception as e:
            errors.append({"row_index": int(idx), "error": str(e)})

    try:
        if objs:
            session.add_all(objs)
            session.commit()
            inserted = len(objs)
    except Exception as e:
        session.rollback()
        errors.append({"db_error": str(e)})
    finally:
        session.close()

    return {"inserted": inserted, "errors": errors}


if __name__ == '__main__':
    # quick smoke test (run from backend directory or with PYTHONPATH set to project root)
    import os
    test_csv = os.path.expanduser(r"~\Downloads\Chase7561_Activity20250101_20251031_20251031.CSV")
    if os.path.exists(test_csv):
        df = pd.read_csv(test_csv, dtype=str)
        create_tables()
        res = insert_df_transactions(df, customer_id='unknown')
        print(res)
    else:
        print(f"Test CSV not found at {test_csv}. Skipping smoke test.")
