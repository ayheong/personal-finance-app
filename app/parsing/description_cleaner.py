import re
import os
import yaml
from rapidfuzz import fuzz


def load_keywords(file_path="categories.yaml"):
    file_path = os.path.abspath(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Keyword file not found: {file_path}")
    with open(file_path, "r") as stream:
        keywords = yaml.safe_load(stream)
    if not isinstance(keywords, dict):
        raise ValueError("YAML file must contain a dictionary with match -> category")
    return keywords

def clean_description(desc):
    desc = desc.upper().strip()
    desc = re.sub(r"\s+", " ", desc)
    desc = re.sub(r"[^\w\s]", "", desc)
    desc = re.sub(r"\d+", "", desc)
    return desc

def fuzzy_match_description(desc, keyword_map, threshold=80):
    desc_clean = clean_description(desc)
    best_match = ("uncategorized", "uncategorized", 0)  # (simplified, category, score)

    for keyword, category in keyword_map.items():
        score = fuzz.partial_ratio(desc_clean, keyword.upper())
        if score > best_match[2] and score > threshold:
            best_match = (keyword, category, score)

    return best_match[0], best_match[1]  # simplified_description, category


def fuzzy_categorize(df, threshold=80, keyword_file="categories.yaml"):
    keyword_map = load_keywords(keyword_file)
    matches = df["description"].apply(lambda x: fuzzy_match_description(x, keyword_map, threshold))

    df["simplified_description"] = matches.apply(lambda x: x[0])
    df["category"] = matches.apply(lambda x: x[1])

    return df
