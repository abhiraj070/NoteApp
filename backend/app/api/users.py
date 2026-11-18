from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schema import User
from .dto import UserOut, UserUpdate
from .security import clear_cookies, current_user, hash_password


router = APIRouter(prefix="/users", tags=["Profile"])


@router.get("/me", response_model=UserOut)
def read_profile(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_profile(data: UserUpdate, response: Response, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one field to update")
    if "name" in changes:
        user.name = changes["name"]
    if "username" in changes:
        user.username = changes["username"].lower()
    if "password" in changes:
        user.password = hash_password(changes["password"])
        user.refreshtoken = None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username is already taken")
    if "password" in changes:
        clear_cookies(response)
    return user


@router.delete("/me", status_code=204)
def delete_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(user)
    db.commit()
    response = Response(status_code=204)
    clear_cookies(response)
    return response
