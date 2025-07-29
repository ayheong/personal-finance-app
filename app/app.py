from flask import Flask, request, jsonify
import pandas as pd
from parsing.parser_main import match_config
from parsing.description_cleaner import fuzzy_categorize
from db.db import save_transactions
from db.db import get_transactions

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    user_id = request.form.get("user_id", "default_user")

    try:
        df = match_config(file)
        df["user_id"] = user_id
        df = fuzzy_categorize(df)
        save_transactions(df)
        return jsonify({'message': 'Transactions saved successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transactions/<user_id>', methods=['GET'])
def get_user_transactions(user_id):
      try:
          transactions = get_transactions(user_id)
          return jsonify({'transactions': transactions})
      except Exception as e:
          return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)