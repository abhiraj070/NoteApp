from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schema import User
from .dto import Login, Register, UserOut
from .security import (clear_cookies, decode_token, hash_password, new_tokens,
                       set_tokens, token_hash, verify_password)


router = APIRouter(prefix="/auth", tags=["Authentication"])
# Reduce username-based timing differences for unsuccessful login attempts.
DUMMY_PASSWORD_HASH = hash_password("unused-dummy-password")


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: Register, db: Session = Depends(get_db)):
    user = User(name=data.name, username=data.username.lower(), password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username is already taken")
    db.refresh(user)
    return user


@router.post("/login", response_model=UserOut)
def login(data: Login, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username.strip().lower()).first()
    valid = verify_password(data.password, user.password if user else DUMMY_PASSWORD_HASH)
    if not user or not valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access, refresh, digest = new_tokens(user.id)
    user.refreshtoken = digest
    db.commit()
    set_tokens(response, access, refresh)
    return user


@router.post("/refresh")
def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Refresh token required")
    payload = decode_token(refresh, "refresh")
    access, replacement, digest = new_tokens(int(payload["sub"]))
    # Atomically consume the old token so concurrent refreshes cannot replay it.
    changed = db.query(User).filter(User.id == int(payload["sub"]),
                                    User.refreshtoken == token_hash(refresh)).update(
                                        {User.refreshtoken: digest}, synchronize_session=False)
    if not changed:
        db.rollback()
        raise HTTPException(status_code=401, detail="Session has been revoked")
    db.commit()
    set_tokens(response, access, replacement)
    return {"message": "Session refreshed"}


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db)):
    # Logout is idempotent, including when a browser has missing/expired cookies.
    for name, kind in (("refresh_token", "refresh"), ("access_token", "access")):
        token = request.cookies.get(name)
        if not token:
            continue
        try:
            payload = decode_token(token, kind)
        except HTTPException:
            continue
        digest = token_hash(token) if kind == "refresh" else payload.get("sid")
        if isinstance(digest, str):
            db.query(User).filter(User.id == int(payload["sub"]), User.refreshtoken == digest).update(
                {User.refreshtoken: None}, synchronize_session=False)
    db.commit()
    response = Response(status_code=204)
    clear_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    return response
