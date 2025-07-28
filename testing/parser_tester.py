import os
import pandas as pd
from parsing.parser_main import match_config
from parsing.description_cleaner import fuzzy_categorize

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_FOLDER = os.path.join(PROJECT_ROOT, "testing", "sample_data")
CONFIG_FOLDER = os.path.join(PROJECT_ROOT, "parsing", "csv_formats")
KEYWORD_FILE = os.path.join(PROJECT_ROOT, "parsing", "categories", "description_keywords.yaml")

def run_test(csv_filename):
    csv_path = os.path.join(CSV_FOLDER, csv_filename)

    try:
        df = match_config(csv_path, config_folder=CONFIG_FOLDER)
        print(f"Successfully parsed {csv_filename}")
        df = fuzzy_categorize(df, keyword_file=KEYWORD_FILE)
        print(f"Successfully categorized {csv_filename}")
        df.to_csv("output_debug.csv", index=False)
    except Exception as e:
        print(f"Failed to parse {csv_filename}: {e}")

if __name__ == "__main__":
    files = ["Checking1.csv", "Chase0562_Activity_20250727.csv"]
    for file in files:
        run_test(file)