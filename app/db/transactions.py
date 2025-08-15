import pandas as pd
from .db import collection


def save_transactions(df: pd.DataFrame, user_id: str = "default_user") -> None:
    """Save transactions to the database for the given user."""
    if df.empty:
        print("DataFrame is empty. Skipping save.")
        return

    try:
        df["user_id"] = user_id
        records = df.to_dict(orient="records")
        collection.insert_many(records)
        print(f"Inserted {len(records)} transactions for user '{user_id}'")
    except Exception as e:
        print(f"Error saving transactions: {e}")


def get_transactions(user_id: str) -> list:
    """Retrieve all transactions for the given user."""
    query = {"user_id": user_id}
    results = list(collection.find(query, {"_id": 0}))
    return results
