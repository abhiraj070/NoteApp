from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schema import Notes, User
from .dto import NoteInput, NoteOut
from .security import current_user


router = APIRouter(prefix="/notes", tags=["Notes"])


def owned_note(note_id, user, db):
    note = db.query(Notes).filter(Notes.id == note_id, Notes.user_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=NoteOut, status_code=201)
def create_note(data: NoteInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    note = Notes(content=data.content, user_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=List[NoteOut])
def list_notes(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Notes).filter(Notes.user_id == user.id).order_by(Notes.id.desc()).offset(offset).limit(limit).all()


@router.get("/{note_id}", response_model=NoteOut)
def read_note(note_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return owned_note(note_id, user, db)


@router.put("/{note_id}", response_model=NoteOut)
@router.patch("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    note = owned_note(note_id, user, db)
    note.content = data.content
    db.commit()
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    note = owned_note(note_id, user, db)
    db.delete(note)
    db.commit()
    return Response(status_code=204)
