from fastapi import FastAPI

from . import schema  # Register the ORM models with the shared database metadata.


app = FastAPI(title="NotesAPP")


@app.get("/health")
def health():
    return {"status": "ok"}
