import re
import os
import yaml
from rapidfuzz import fuzz

def load_keywords(file_path=None):
    if file_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "categories", "description_keywords.yaml")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Keyword file not found: {file_path}")
    with open(file_path, "r") as stream:
        keywords = yaml.safe_load(stream)
    if not isinstance(keywords, dict):
        raise ValueError("YAML file must contain a dictionary with match -> category")
    return keywords

GENERIC_WORDS = [
    "PAYMENT", "PURCHASE", "WITHDRAWAL", "TRANSFER", "DEPOSIT",
    "RECURRING", "SUBSCRIPTION", "ORDER", "REF", "TXN", "TRANS",
    "WEB", "MOBILE", "CHARGE", "AUTHORIZED", "POS", "ACH", "CHECK",
    "ATM", "CARD", "CREDIT", "DEBIT", "BANK", "ONLINE", "TO", "FROM", "ON"
]

STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}
def clean_description(desc):
    # Normalize
    desc = desc.upper().strip()

    # Remove "CARD 1234" patterns
    desc = re.sub(r"CARD\s*\d+", "", desc)

    # Remove date patterns like "AUTHORIZED ON 07/23"
    desc = re.sub(r"AUTHORIZED\s+ON\s+\d{2}/\d{2}", "", desc)

    # Remove common generic banking words
    for word in GENERIC_WORDS:
        desc = re.sub(rf"\b{word}\b", "", desc)

    # Remove digits and punctuation
    desc = re.sub(r"\d+", "", desc)
    desc = re.sub(r"[^\w\s]", "", desc)

    # Remove leftover single-letter tokens
    desc = re.sub(r"\b[A-Z]\b", "", desc)

    # Remove state codes
    for state in STATE_CODES:
        desc = re.sub(rf"\b{state}\b", "", desc)

    # Collapse repeated words (e.g., "CAREERFLOWAI CAREERFLOWAI")
    words = desc.split()
    deduped = []
    for i, word in enumerate(words):
        if i == 0 or word != words[i - 1]:
            deduped.append(word)
    desc = " ".join(deduped)

    # Final cleanup of extra spaces
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc

def fuzzy_match_description(desc, keyword_map, threshold=80):
    desc_clean = clean_description(desc)
    best_match = ("uncategorized", "uncategorized", 0)  # (simplified, category, score)

    for keyword, category in keyword_map.items():
        score = fuzz.partial_ratio(desc_clean, keyword.upper())
        if score > best_match[2] and score > threshold:
            best_match = (keyword, category, score)

    return best_match[0], best_match[1]  # simplified_description, category



def fuzzy_categorize(df, threshold=80, keyword_file=None, use_fuzzy=False):
    if not use_fuzzy:
        df["simplified_description"] = df["description"].apply(clean_description)
        df["category"] = "uncategorized"
        return df

    # Use fuzzy matching
    keyword_map = load_keywords(keyword_file)
    matches = df["description"].apply(lambda x: fuzzy_match_description(x, keyword_map, threshold))
    df["simplified_description"] = matches.apply(lambda x: x[0])
    df["category"] = matches.apply(lambda x: x[1])
    return df
