# Notes frontend

Next.js App Router + React + TypeScript. The backend owns authentication and
note permissions. The frontend keeps tokens in HttpOnly cookies and never in
local storage. `/api` requests are proxied to FastAPI through Next.js.

## Deploy on Vercel

Import `abhiraj070/NoteApp` from branch `main` and select the repository root.
The root `vercel.json` explicitly defines the `frontend` Next.js service and
routes requests to it. This avoids auto-detecting the Python apps at the
repository root and in `backend` as the frontend deployment.

Add `BACKEND_URL` in Vercel's environment variables with the deployed FastAPI
HTTPS origin (without `/api`). The backend must be hosted separately. Add the
Vercel frontend origin to the backend's `ALLOWED_ORIGINS` and use
`COOKIE_SECURE=true` on the backend. Redeploy after changing `BACKEND_URL`.
Do not use localhost as the backend URL in a hosted deployment.

## Run locally

From the project root, start FastAPI in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000. `/auth` has login and signup; `/` is the protected
notes workspace. Signup automatically logs in after creating an account.

The backend `.env` must include `http://127.0.0.1:3000` (and optionally
`http://localhost:3000`) in `ALLOWED_ORIGINS`. Restart FastAPI after changing it.
Use `COOKIE_SECURE=false` for local HTTP. Use `true` with HTTPS in production.

To use another backend, copy `.env.example` to `.env.local`, set `BACKEND_URL`,
and restart Next.js. Add the frontend's origin to the backend's allowed origins.
Use the same hostname consistently so browser cookies stay on the correct host.

## Features

- Signup, login, logout, automatic token refresh, and session checks.
- Central searchable notes list, editor, create, update, and delete.
- Fetches every page of the signed-in user's notes.
- Profile updates and account deletion with confirmation.
- Unsaved-change prompts, loading states, errors, empty states, responsive UI.

The first line of a note is displayed as its title. Content is stored as plain
text using the existing backend schema. Notes are saved explicitly with Save.
Profile password changes sign the user out. Deleting an account deletes its notes.

## Verify / build

```powershell
npm run typecheck
npm run build
npm start
```
