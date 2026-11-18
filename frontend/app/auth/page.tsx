"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, User } from "@/lib/api";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    let active = true;
    api<User>("/users/me").then(() => { if (active) router.replace("/"); }).catch(() => { if (active) setChecking(false); });
    return () => { active = false; };
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setBusy(true);
    const data = new FormData(event.currentTarget);
    const credentials = { username: String(data.get("username")).trim(), password: String(data.get("password")) };
    try {
      if (mode === "signup") {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ ...credentials, name: String(data.get("name")).trim() }) });
        setMode("login");
      }
      await api("/auth/login", { method: "POST", body: JSON.stringify(credentials) });
      router.replace("/");
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not sign in. Please try again."); setBusy(false); }
  }

  if (checking) return <main className="loading-screen"><p>Loading…</p></main>;
  return <main className="auth-page">
    <h1>Notes</h1>
    <div className="auth-tabs"><button type="button" aria-pressed={mode === "login"} disabled={busy} onClick={() => { setMode("login"); setError(""); }}>Log in</button><button type="button" aria-pressed={mode === "signup"} disabled={busy} onClick={() => { setMode("signup"); setError(""); }}>Sign up</button></div>
    <form onSubmit={submit}>
      {mode === "signup" && <label className="field">Name<input name="name" autoComplete="name" required maxLength={100} disabled={busy} /></label>}
      <label className="field">Username<input name="username" autoComplete="username" required minLength={mode === "signup" ? 3 : 1} maxLength={50} pattern={mode === "signup" ? "[A-Za-z0-9_]+" : undefined} title="Letters, numbers, and underscores" disabled={busy} /></label>
      <label className="field">Password<input name="password" type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} minLength={mode === "signup" ? 8 : 1} maxLength={128} required disabled={busy} /></label>
      {mode === "signup" && <p className="help">Use at least 8 characters.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Log in" : "Sign up"}</button>
    </form>
  </main>;
}
