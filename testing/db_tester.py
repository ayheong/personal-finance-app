import pandas as pd
from app.db.db import save_transactions, get_transactions
import pprint

# dummy data
data = [
    {
        "date": "2025-07-25",
        "amount": -1646.98,
        "description": "CHASE CREDIT CRD AUTOPAY PPD ID: 4760039224",
        "simplified_description": "Chase",
        "category": "Bank"
    },
    {
        "date": "2025-07-26",
        "amount": -6.45,
        "description": "Starbucks 1234 Sacramento CA",
        "simplified_description": "Starbucks",
        "category": "Coffee"
    }
]

df = pd.DataFrame(data)

user_id = "test_user_001"
# Save to MongoDB under test user
# save_transactions(df, user_id=user_id)

transactions = get_transactions(user_id=user_id)

print(f"Retrieved {len(transactions)} transactions for user {user_id}:\n")
pprint.pprint(transactions)