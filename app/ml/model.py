from typing import List, Optional
import re
import torch
import numpy as np
import os
from transformers import BertTokenizer, BertForSequenceClassification

CATEGORIES: List[str] = [
    "Housing",
    "Utilities & Bills",
    "Food & Dining",
    "Transportation",
    "Shopping & Retail",
    "Subscriptions & Memberships",
    "Transfers & Payments",
    "Income & Deposits",
    "Health & Wellness",
    "Travel & Entertainment",
    "Other",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = "perplexingpanda/bert_bank_transaction_categorizer"

_OVERRIDES = {
    r"\b(SAFEWAY|COSTCO|WALMART|TRADER JOE'?S?|WHOLE FOODS|KROGER|RALPHS|VONS|ALBERTSONS|TARGET|SPROUTS|H[- ]?MART|99 RANCH|SUPERMARKET|GROCERY|MARKET)\b": "Food & Dining",
    r"\b(STARBUCKS|DUNKIN|COFFEE|CAF[EÉ]|MCDONALD'?S|BURGER KING|CHICK[- ]?FIL[- ]?A|WENDY'?S|TACO BELL|DOMINO'?S|PIZZA HUT|SUBWAY|PANERA|CHIPOTLE|SHAKE SHACK|SUSHI|BBQ|IHOP|DENNY'?S|WINGSTOP|RESTAURANT|BAKERY|TEASPOON|JAMBA)\b": "Food & Dining",
    r"\b(NETFLIX|SPOTIFY|HULU|DISNEY(?:\+| PLUS)|YOUTUBE(?: PREMIUM)?|AMAZON PRIME|APPLE MUSIC|APPLE TV|OPENAI|CHATGPT|DISCORD|RENDER\.?COM?)\b": "Subscriptions & Memberships",
    r"\b(COMCAST|XFINITY|VERIZON|AT&T|T[- ]?MOBILE|SPRINT|SPECTRUM|CABLE|INTERNET|UTILITY|UTILITIES|PG&E|PGE)\b": "Utilities & Bills",
    r"\b(AMAZON|EBAY|ETSY|BEST BUY|APPLE STORE|APPLE\.COM|GOOGLE STORE|MACY'?S|NORDSTROM|KOHL'?S|TJ MAXX|MARSHALLS|ROSS|SEPHORA|ULTA|FOOT LOCKER|NIKE|ADIDAS|LULU ?LEMON|LULULEMON|OUTLET|BOUTIQUE)\b": "Shopping & Retail",
    r"\b(UBER|LYFT|TAXI|SCOOTER|BIKE SHARE|SHELL|CHEVRON|EXXON|MOBIL|BP|ARCO|CIRCLE K|VALERO|CONOCO|GAS( STATION)?|FUEL|PARKING|GARAGE|CLIPPER|BART|MUNI|CALTRAIN|AMTRAK)\b": "Transportation",
    r"\b(DELTA|UNITED|SOUTHWEST|JETBLUE|ALASKA AIR|AIRLINES|AIRPORT|HOTEL|AIRBNB|BOOKING\.COM|EXPEDIA|CAR RENTAL|AVIS|HERTZ|ENTERPRISE|CONCERT|FESTIVAL|EVENT)\b": "Travel & Entertainment",
    r"\b(IRS|TAX|TOLLS?|E[- ]?ZPASS|FASTRAK|DMV|COURT FEE|PARKING TICKET|FINE)\b": "Other",
    r"\b(DIRECT DEPOSIT|PAYROLL|PAYCHECK|SALARY|WAGES|REFUND|REBATE|REIMBURSEMENT|CASHBACK)\b": "Income & Deposits",
    r"\b(VENMO|ZELLE|CASH ?APP|PAYPAL TRANSFER|WIRE|ACH|BANK TRANSFER|TRANSFER|WITHDRAWAL|ATM|CASHOUT|ZELLE FROM|ZELLE TO)\b": "Transfers & Payments",
    r"\b(CREDIT CARD PAYMENT|CARD PAYMENT|CREDIT CARD)\b": "Transfers & Payments",
}

_OVERRIDES = [(re.compile(pat, re.IGNORECASE), cat) for pat, cat in _OVERRIDES.items()]

_tokenizer = None
_model = None
_id2label_trained = None

def _ensure_bert():
    global _tokenizer, _model, _id2label_trained
    if _tokenizer is not None and _model is not None and _id2label_trained is not None:
        return

    # load tokenizer and model
    _tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
    _model = BertForSequenceClassification.from_pretrained(MODEL_DIR)
    _model.eval()
    _model.to("cuda" if torch.cuda.is_available() else "cpu")

    # map ids to label in model config, use CATEGORIES elsewise
    if getattr(_model.config, "id2label", None):
        _id2label_trained = {int(k): v for k, v in _model.config.id2label.items()}
    else:
        _id2label_trained = {
            i: CATEGORIES[i] if i < len(CATEGORIES) else f"Label_{i}"
            for i in range(_model.config.num_labels)
        }

# hardcoded overrides for known vendors and text descriptions
def _override(clean_text: str, allowed: set) -> Optional[str]:
    for rx, cat in _OVERRIDES:
        if rx.search(clean_text) and cat in allowed:
            return cat
    return None

# ensure labels
def _map_trained_to_app(trained_label: str) -> str:
    return trained_label if trained_label in CATEGORIES else "Other"

# ensure predicted category is allowed
def _pick_allowed(mapped_probs: list[tuple], allowed: set) -> str:
    for cat, _p in mapped_probs:
        if cat in allowed:
            return cat
    return "Other"

def predict_labels(texts: List[str], candidate_labels: Optional[List[str]] = None, *, batch_size: int = 16) -> List[str]:
    if not texts:
        return []
    _ensure_bert()
    labels = candidate_labels or CATEGORIES
    allowed = set(labels)
    results: List[Optional[str]] = []
    to_classify: List[str] = []
    mapping: List[int] = []

    # try overrides
    for i, raw in enumerate(texts):
        hit = _override(raw or "", allowed)
        if hit:  # override
            results.append(hit)
        else:  # placeholder
            results.append(None)
            to_classify.append(raw or "")
            mapping.append(i)
    # classify
    if to_classify:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        for start in range(0, len(to_classify), batch_size):
            chunk = to_classify[start : start + batch_size]
            # tokenize batch
            enc = _tokenizer(chunk, padding=True, truncation=True, max_length=160, return_tensors="pt")
            enc = {k: v.to(device) for k, v in enc.items()}

            # inference
            with torch.no_grad():
                logits = _model(**enc).logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()

            # map predictions back to categories
            for row_probs, idx in zip(probs, mapping[start : start + len(probs)]):
                order = np.argsort(-row_probs)
                ranked = []
                for k in order:
                    trained_label = _id2label_trained.get(int(k), f"Label_{int(k)}")
                    app_cat = _map_trained_to_app(trained_label)
                    ranked.append((app_cat, float(row_probs[k])))
                results[idx] = _pick_allowed(ranked, allowed)
    return [c if c is not None else "Other" for c in results]  # return other if bad

def predict_label(text: str, candidate_labels: Optional[List[str]] = None) -> str:
    return predict_labels([text], candidate_labels=candidate_labels, batch_size=1)[0]
