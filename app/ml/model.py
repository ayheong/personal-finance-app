from typing import List, Optional
from transformers import pipeline
import re

CATEGORIES: List[str] = [
    "Income",
    "Transfer",
    "Utilities",
    "Food & Dining",
    "Shopping",
    "Transport & Travel",
    "Fees & Taxes",
    "Other",
]

MODEL_NAME = "typeform/distilbert-base-uncased-mnli"

_RAILS_OVERRIDES_RAW = {
    r"\b(DIRECT DEPOSIT|PAYROLL|PAYCHECK|SALARY|WAGES|REFUND|REBATE|REIMBURSEMENT|CASHBACK)\b": "Income",
    r"\b(VENMO|ZELLE|CASH ?APP|PAYPAL TRANSFER|WIRE|ACH|BANK TRANSFER|TRANSFER|WITHDRAWAL|ATM|CASHOUT|ZELLE FROM|ZELLE TO)\b": "Transfer",
}

_MERCHANT_OVERRIDES_RAW = {
    r"\b(SAFEWAY|COSTCO|WALMART|TRADER JOE'?S?|WHOLE FOODS|KROGER|RALPHS|VONS|ALBERTSONS|TARGET|SPROUTS|H[- ]?MART|99 RANCH|SUPERMARKET|GROCERY|MARKET)\b": "Food & Dining",
    r"\b(STARBUCKS|DUNKIN|COFFEE|CAF[EÉ]|MCDONALD'?S|BURGER KING|CHICK[- ]?FIL[- ]?A|WENDY'?S|TACO BELL|DOMINO'?S|PIZZA HUT|SUBWAY|PANERA|CHIPOTLE|SHAKE SHACK|SUSHI|BBQ|IHOP|DENNY'?S|WINGSTOP|RESTAURANT|BAKERY|TEASPOON|JAMBA)\b": "Food & Dining",

    r"\b(NETFLIX|SPOTIFY|HULU|DISNEY(?:\+| PLUS)|YOUTUBE(?: PREMIUM)?|AMAZON PRIME|APPLE MUSIC|APPLE TV|OPENAI|CHATGPT|DISCORD|RENDER\.?COM?)\b": "Bills & Utilities",
    r"\b(COMCAST|XFINITY|VERIZON|AT&T|T[- ]?MOBILE|SPRINT|SPECTRUM|CABLE|INTERNET|UTILITY|UTILITIES|PG&E|PGE)\b": "Bills & Utilities",

    r"\b(AMAZON|EBAY|ETSY|BEST BUY|APPLE STORE|APPLE\.COM|GOOGLE STORE|MACY'?S|NORDSTROM|KOHL'?S|TJ MAXX|MARSHALLS|ROSS|SEPHORA|ULTA|FOOT LOCKER|NIKE|ADIDAS|LULU ?LEMON|LULULEMON|OUTLET|BOUTIQUE)\b": "Shopping",

    r"\b(TESLA|UBER|LYFT|TAXI|SCOOTER|BIKE SHARE|SHELL|CHEVRON|EXXON|MOBIL|BP|ARCO|CIRCLE K|VALERO|CONOCO|GAS( STATION)?|FUEL|PARKING|GARAGE|CLIPPER|BART|MUNI|CALTRAIN|AMTRAK|DELTA|UNITED|SOUTHWEST|JETBLUE|ALASKA AIR|AIRLINES|AIRPORT|HOTEL|AIRBNB|BOOKING\.COM|EXPEDIA|CAR RENTAL|AVIS|HERTZ|ENTERPRISE)\b": "Transport & Travel",

    r"\b(IRS|TAX|TOLLS?|E[- ]?ZPASS|FASTRAK|DMV|COURT FEE|PARKING TICKET|FINE)\b": "Fees & Taxes",
}

_MERCHANT_OVERRIDES = [(re.compile(pat, re.IGNORECASE), cat) for pat, cat in _MERCHANT_OVERRIDES_RAW.items()]
_RAILS_OVERRIDES = [(re.compile(pat, re.IGNORECASE), cat) for pat, cat in _RAILS_OVERRIDES_RAW.items()]

_classifier = None


def _ensure_classifier():
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            task="zero-shot-classification",
            model=MODEL_NAME,
            device=-1,  # CPU
        )


def _preclean(desc: str) -> str:
    if not desc:
        return ""
    t = desc.upper()
    t = re.sub(r"\b(PURCHASE|RECURRING|INTERNATIONAL|AUTHORIZED|PAYMENT)\b", " ", t)
    t = re.sub(r"\bON\s+\d{2}/\d{2}\b", " ", t)
    t = re.sub(r"\bCARD\s*\d+\b", " ", t)
    t = re.sub(r"\d{6,}", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _choose_override(clean_text: str, allowed: set) -> Optional[str]:
    for rx, cat in _RAILS_OVERRIDES:
        if rx.search(clean_text) and cat in allowed:
            return cat
    for rx, cat in _MERCHANT_OVERRIDES:
        if rx.search(clean_text) and cat in allowed:
            return cat
    return None


def predict_labels(
    texts: List[str],
    candidate_labels: Optional[List[str]] = None,
    *,
    multi_label: bool = False,
    batch_size: int = 16,
) -> List[str]:
    if not texts:
        return []

    _ensure_classifier()
    labels = candidate_labels or CATEGORIES
    allowed = set(labels)

    results: List[Optional[str]] = []
    to_classify: List[str] = []
    mapping: List[int] = []

    for i, raw in enumerate(texts):
        clean = _preclean(raw or "")
        hit = _choose_override(clean, allowed)
        if hit:
            results.append(hit)
        else:
            results.append(None)
            to_classify.append(clean if clean else (raw or ""))
            mapping.append(i)

    if to_classify:
        for start in range(0, len(to_classify), batch_size):
            chunk = to_classify[start : start + batch_size]
            out = _classifier(chunk, candidate_labels=labels, multi_label=multi_label)
            if isinstance(out, dict):
                out = [out]
            for r, idx in zip(out, mapping[start : start + len(out)]):
                scores = r["scores"]
                best_idx = int(max(range(len(scores)), key=lambda k: scores[k]))
                results[idx] = r["labels"][best_idx]

    return [c if c is not None else "Other" for c in results]


def predict_label(
    text: str,
    candidate_labels: Optional[List[str]] = None,
    *,
    multi_label: bool = False,
) -> str:
    return predict_labels(
        [text],
        candidate_labels=candidate_labels,
        multi_label=multi_label,
        batch_size=1,
    )[0]
