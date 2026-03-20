import hashlib
import jwt
import datetime
from flask import current_app


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(username: str) -> str:
    payload = {
        'sub': username,
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=current_app.config.get('JWT_EXPIRATION_HOURS', 24)
        ),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
