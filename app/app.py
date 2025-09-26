from flask import Flask, request, jsonify

from ml.model import predict_labels
from auth import require_auth, auth_bp, bcrypt
from db.transactions import save_transactions, get_transactions
from pandas.errors import ParserError
from parsing.parser_main import match_config

app = Flask(__name__, static_folder="static", static_url_path="")
bcrypt.init_app(app)
app.register_blueprint(auth_bp)

@app.get("/")
def index():
    return app.send_static_file("index.html")

@app.route("/upload", methods=["POST"])
@require_auth
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    csv_type = request.form.get('csv_type')
    if not csv_type:
        return jsonify({'error': 'No csv type selected'}), 400
    user_id = str(request.user["user_id"])
    try:
        df = match_config(file, csv_type)
        df["user_id"] = user_id

        if "category" in df:
            mask = df["category"].isna()
            if mask.any():
                labels = predict_labels(df.loc[mask, "description"].tolist())
                df.loc[mask, "category"] = labels
        else:
            labels = predict_labels(df["description"].tolist())
            df["category"] = labels
        save_transactions(df, user_id)
        return jsonify({'message': 'Transactions saved successfully!'})
    except (KeyError, ValueError, ParserError):
        return jsonify({
            'error': "Upload failed, the file format doesn’t match the account type you selected."
        }), 400
    except Exception as e:
        import logging
        logging.exception("Unexpected error during upload")
        return jsonify({
            'error': "Something went wrong while processing your file. Please try again later."
        }), 500

@app.route("/transactions", methods=["GET"])
@require_auth
def get_user_transactions():
    user_id = str(request.user["user_id"])
    try:
        transactions = get_transactions(user_id)
        return jsonify({"transactions": transactions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
