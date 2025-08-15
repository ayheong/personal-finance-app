from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from functools import wraps

from db.users import get_user_by_username, create_user

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if get_user_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    create_user(username, email, pw_hash)
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = get_user_by_username(username)
    if not user or not bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = jwt.encode({
        'user_id': str(user['_id']),
        'username': user['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, JWT_SECRET, algorithm='HS256')

    return jsonify({'token': token})


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or malformed token'}), 403
        token = auth.split(' ', 1)[1]

        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            # Prefer flask.g for request-scoped data
            from flask import g
            g.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 403

        return f(*args, **kwargs)
    return decorated