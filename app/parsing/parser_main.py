import os
import pandas as pd
import yaml

pd.set_option('display.max_colwidth', None)

# load formats of bank CSVs into dictionary
def load_configs(folder="csv_formats"):
    configs = {}
    for file in os.listdir(folder):
        if file.endswith(".yaml"):
            with open(os.path.join(folder, file), "r") as stream:
                configs[file.replace(".yaml", "")] = yaml.safe_load(stream)
    return configs

# parse the csv with determined format
def parse_csv(csv_path, config):
    # check header
    if config["has_header"]:
        df = pd.read_csv(csv_path, index_col=False)
        df.columns = [col.strip().lower() for col in df.columns]
        # for new column names, original column names
        for normalized_col, original_col in config["match_columns"].items():
            for col in df.columns:
                if col in [a.lower() for a in original_col]:
                    df = df.rename(columns={col: normalized_col})
                    break
    else:
        df = pd.read_csv(csv_path, header=None)
        df.columns = config["columns"]

    if "date_format" in config:
        df["date"] = pd.to_datetime(df["date"], format=config["date_format"])
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["description"] = df["description"].astype(str).str.strip().str.upper()

    return df[["date", "amount", "description"]].dropna()

# determines the bank with matching format
def match_config(csv_path, config_folder="csv_formats"):
    all_configs = load_configs(config_folder)
    last_exception = None

    for bank, config in all_configs.items():
        try:
            df = parse_csv(csv_path, config)
            return df
        except (pd.errors.ParserError, KeyError, ValueError) as e:
            last_exception = e  # capture the most recent failure
            continue

    raise ValueError(f"Could not parse csv with any known formats. Last error: {last_exception}")
