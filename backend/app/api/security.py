import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schema import User


ACCESS_SECONDS = 15 * 60
REFRESH_SECONDS = 7 * 24 * 60 * 60
PASSWORD_ITERATIONS = 600000


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(PASSWORD_ITERATIONS, salt, digest.hex())


def verify_password(password, stored):
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError, AttributeError):
        return False


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def secret_key():
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a random secret of at least 32 characters in backend/.env")
    return secret


def create_token(user_id, token_type, seconds, **claims):
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": token_type, "iat": now,
               "exp": now + timedelta(seconds=seconds), "jti": secrets.token_hex(16)}
    payload.update(claims)
    return jwt.encode(payload, secret_key(), algorithm="HS256")


def decode_token(token, expected_type):
    try:
        payload = jwt.decode(token, secret_key(), algorithms=["HS256"],
                             options={"require_exp": True, "require_iat": True, "require_sub": True, "require_jti": True})
        if payload.get("type") != expected_type or int(payload["sub"]) <= 0:
            raise ValueError("Invalid token")
        return payload
    except (JWTError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def cookie_options():
    return {"httponly": True, "secure": os.getenv("COOKIE_SECURE", "true").lower() == "true",
            "samesite": "lax", "path": "/"}


def clear_cookies(response):
    for name in ("access_token", "refresh_token"):
        response.delete_cookie(name, **cookie_options())


def set_tokens(response, access, refresh):
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie("access_token", access, max_age=ACCESS_SECONDS, **cookie_options())
    response.set_cookie("refresh_token", refresh, max_age=REFRESH_SECONDS, **cookie_options())


def new_tokens(user_id):
    refresh = create_token(user_id, "refresh", REFRESH_SECONDS)
    digest = token_hash(refresh)
    access = create_token(user_id, "access", ACCESS_SECONDS, sid=digest)
    return access, refresh, digest


def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    payload = decode_token(token, "access")
    user = db.get(User, int(payload["sub"]))
    sid = payload.get("sid")
    if not user or not user.refreshtoken or not isinstance(sid, str) or not hmac.compare_digest(user.refreshtoken, sid):
        raise HTTPException(status_code=401, detail="Session has been revoked")
    return user
