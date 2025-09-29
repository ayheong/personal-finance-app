import hashlib
import pandas as pd
from pymongo.errors import BulkWriteError
from .db import collection  # has the unique index on fingerprint already

def _norm_date(val) -> str:
    return pd.to_datetime(val).strftime("%Y-%m-%d")

def _norm_amount_cents(val) -> int:
    return int(round(float(val) * 100))

def _row_fingerprint(row) -> str:
    user_id = str(row.get("user_id", "")).strip()
    date_s  = _norm_date(row["date"])
    cents   = _norm_amount_cents(row["amount"])
    desc = (row.get("description") or "").strip().upper()
    return hashlib.sha1(f"{user_id}|{date_s}|{cents}|{desc}".encode("utf-8")).hexdigest()

def save_transactions(df: pd.DataFrame, user_id: str | None = None) -> int:
    if df.empty:
        return 0

    if user_id is not None and "user_id" not in df.columns:
        df["user_id"] = user_id

    # Build fingerprints + drop in-batch duplicates
    df["fingerprint"] = df.apply(_row_fingerprint, axis=1)
    df = df.drop_duplicates(subset=["fingerprint"])

    records = df.to_dict("records")
    if not records:
        return 0

    try:
        res = collection.insert_many(records, ordered=False)
        return len(res.inserted_ids)
    except BulkWriteError as bwe:
        # Count successful inserts by subtracting duplicate key errors
        dup_errors = sum(1 for w in bwe.details.get("writeErrors", []) if w.get("code") == 11000)
        return max(0, len(records) - dup_errors)

def get_transactions(user_id: str) -> list:
    query = {"user_id": user_id}
    return list(collection.find(query, {"_id": 0}))
