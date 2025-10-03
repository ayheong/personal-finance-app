import os
import pandas as pd
import yaml

def load_configs(folder="csv_formats"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir, folder)

    configs = {}
    for file in os.listdir(config_dir):
        if file.endswith(".yaml"):
            with open(os.path.join(config_dir, file), "r") as stream:
                configs[file.replace(".yaml", "")] = yaml.safe_load(stream)
    return configs

def normalize(df, csv_type):
    """
    Default to negative for expenses and positives for incoming money amounts.
    Also account for Automatic payments in credit card (remove).
    """
    flipped_csv_types = ["amex_credit"]
    has_automatic_payments = ["chase_credit", "amex_credit"]
    if csv_type in flipped_csv_types:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce") * -1
    if csv_type in has_automatic_payments:
        df = df[~df["description"].str.contains("AUTOMATIC PAYMENT - THANK", case=False, na=False)]
        df = df[~df["description"].str.contains("AUTOPAY PAYMENT - THANK YOU", case=False, na=False)]

    return df


def parse_csv(file_like, config):
    if config.get("has_header", True):
        df = pd.read_csv(file_like, index_col=False)
        df.columns = [col.strip().lower() for col in df.columns]
        for normalized_col, original_cols in config.get("match_columns", {}).items():
            for col in df.columns:
                if col in [a.lower() for a in original_cols]:
                    df = df.rename(columns={col: normalized_col})
                    break
    else:
        df = pd.read_csv(file_like, header=None)
        df.columns = config["columns"]
    if "date_format" in config:
        df["date"] = pd.to_datetime(df["date"], format=config["date_format"], errors="coerce")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "og_category" in df.columns:
        df["og_category"] = df["og_category"].astype(str).str.strip()
        translate_map = config.get("translate_map", {})
        df["category"] = df["og_category"].map(translate_map).fillna("Other")
    else:
        df["category"] = None
    cols = ["date", "amount", "description", "category"]

    return df[cols]


def match_config(file_like, csv_type, config_folder="csv_formats"):
    all_configs = load_configs(config_folder)
    if csv_type not in all_configs:
        raise ValueError(f"Unsupported csv_type: {csv_type}")
    config = all_configs[csv_type]
    file_like.seek(0)
    df = parse_csv(file_like, config)
    df = normalize(df, csv_type)
    return df
