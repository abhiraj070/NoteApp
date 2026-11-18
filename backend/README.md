# Notes API backend

## Configure Neon

Set `DATABASE_URL` in `.env` to the PostgreSQL connection URL from Neon.
Paste only the URL, without a surrounding `psql` command. Preserve its query
parameters, including `sslmode=require` and `channel_binding` when supplied.
The `.env` file is ignored by Git; `.env.example` is a shareable template.

## Run from the project root (PowerShell)

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\backend\.venv\Scripts\python.exe backend\check_db.py
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

API documentation: http://127.0.0.1:8000/docs

The database check runs `SELECT 1` and does not change the database.
The `/health` route checks that the API is running. Database sessions are
available through `app.db.database.get_db` for future auth, notes, and profile routes.

## Database models

`app/schema/user.py` defines `User` with name, unique username, password (a
string for a future password hash), nullable refreshtoken, and a `Notes`
relationship. `app/schema/notes.py` defines `Notes` with content and a required
user relationship through `user_id`. Each user can own multiple notes.
Deleting a user through the ORM also deletes their notes.

These models define the schema in code. Tables are not created automatically;
apply an Alembic migration before using them against Neon.
