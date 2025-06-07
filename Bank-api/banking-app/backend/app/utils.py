def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password: str, provided_password: str) -> bool:
    return stored_password == hash_password(provided_password)

def generate_token(data: dict) -> str:
    import jwt
    from datetime import datetime, timedelta

    secret_key = "your_secret_key"
    expiration = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode({"exp": expiration, **data}, secret_key, algorithm="HS256")
    return token

def decode_token(token: str) -> dict:
    import jwt

    secret_key = "your_secret_key"
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}