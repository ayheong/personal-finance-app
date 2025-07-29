from flask import Flask, request, jsonify
import pandas as pd
from parsing.parser_main import match_config
from parsing.description_cleaner import fuzzy_categorize
from db.db import save_transactions

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        df = pd.read_csv(file)
        user_id = "test_user"
        df["user_id"] = user_id
        df = fuzzy_categorize(df)
        save_transactions(df)
        return jsonify({'message': 'Transactions saved successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)