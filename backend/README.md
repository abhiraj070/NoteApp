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
.\backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

API documentation: http://127.0.0.1:8000/docs

The database check runs `SELECT 1` and does not change the database.
The `/health` route checks that the API is running. Database sessions are
available through `app.db.database.get_db` for auth, notes, and profile routes.

## Database models

`app/schema/user.py` defines `User` with name, unique username, password (a
string containing a salted PBKDF2-SHA256 password hash), nullable refreshtoken, and a `Notes`
relationship. `app/schema/notes.py` defines `Notes` with content and a required
user relationship through `user_id`. Each user can own multiple notes.
Deleting a user through the ORM also deletes their notes.

These models define the schema in code. Tables are not created automatically;
apply an Alembic migration before using them against Neon.

## Authentication settings

Set `JWT_SECRET_KEY` in `.env` to a random secret of at least 32 characters.
`COOKIE_SECURE=false` supports local HTTP development; set it to `true` for
HTTPS deployments. Tokens are sent only in HttpOnly, SameSite=Lax cookies.
Access tokens expire after 15 minutes; refresh tokens expire after 7 days.
Only a SHA-256 digest of the refresh token is stored in the database.
There is one active session per user: login and refresh replace the session;
logout and password changes revoke it immediately, including access tokens.
Refresh rotates both cookies. Registration creates the account; login separately.

The browser should send requests with `credentials: "include"`. Requests with
an Origin header must come from the API's own origin or a comma-separated
origin listed in `ALLOWED_ORIGINS`. Cross-origin frontends need that setting
for CORS. Cookies use SameSite=Lax, so use a same-site frontend/API deployment.
Changing the password signs the user out. Passwords and tokens are excluded
from profile responses.

## JSON API

| Method | Route | Body / purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | `{"name":"Alice","username":"alice","password":"password123"}` |
| POST | `/api/auth/login` | `{"username":"alice","password":"password123"}`; sets cookies |
| POST | `/api/auth/refresh` | Uses refresh cookie and rotates both tokens |
| POST | `/api/auth/logout` | Clears cookies and removes the stored refresh digest |
| GET | `/api/users/me` | Read current user's profile |
| PATCH | `/api/users/me` | Update name, username, and/or password |
| DELETE | `/api/users/me` | Delete account and its notes |
| POST | `/api/notes` | `{"content":"My note"}` |
| GET | `/api/notes?offset=0&limit=50` | List current user's notes (limit 1–100) |
| GET | `/api/notes/{id}` | Read an owned note |
| PUT / PATCH | `/api/notes/{id}` | `{"content":"Updated note"}` |
| DELETE | `/api/notes/{id}` | Delete an owned note |

Usernames are case-insensitive and stored lowercase. Note access requires
login and is restricted to the owner. Access to another user's note returns
404. Public registration is the create-user operation; profile routes operate
on the authenticated account, without exposing a public user directory.

## Tests

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt httpx==0.24.1
.\backend\.venv\Scripts\python.exe -m unittest backend.tests.test_api -v
```

Tests use an isolated in-memory database and do not change Neon data.

## PyCharm interpreter

This project's PyCharm configuration selects the root `.venv\Scripts\python.exe`.
Install dependencies into that environment when running through PyCharm:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt httpx==0.24.1
```

The root `pyproject.toml` also declares the backend dependencies for IDE sync.
The `backend/.venv` environment used by the commands above remains available.
