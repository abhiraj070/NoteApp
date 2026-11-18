"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Modal } from "@/components/modal";
import { NotesList } from "@/components/notes-list";
import { allNotes, api, ApiError, Note, noteTitle, User } from "@/lib/api";

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [draft, setDraft] = useState(false);
  const [content, setContent] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState<"profile" | "delete-note" | "delete-account" | null>(null);
  const selected = notes.find(note => note.id === selectedId);
  const dirty = draft ? content.length > 0 : !!selected && selected.content !== content;
  const editing = draft || !!selected;

  const handleError = useCallback((err: unknown) => {
    if (err instanceof ApiError && err.status === 401) router.replace("/auth");
    else setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
  }, [router]);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const profile = await api<User>("/users/me");
      setUser(profile);
      const collection = await allNotes();
      setNotes(collection);
      setSelectedId(collection[0]?.id ?? null);
      setContent(collection[0]?.content ?? "");
      setDraft(false);
    } catch (err) { handleError(err); }
    finally { setLoading(false); }
  }, [handleError]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } };
    const shortcut = (event: KeyboardEvent) => {
      if (event.key === "/" && !(event.target instanceof HTMLInputElement) && !(event.target instanceof HTMLTextAreaElement) && !modal) {
        event.preventDefault(); document.querySelector<HTMLInputElement>('input[aria-label="Search your notes"]')?.focus();
      }
    };
    window.addEventListener("beforeunload", beforeUnload); window.addEventListener("keydown", shortcut);
    return () => { window.removeEventListener("beforeunload", beforeUnload); window.removeEventListener("keydown", shortcut); };
  }, [dirty, modal]);
  useEffect(() => { if (notice) { const timer = setTimeout(() => setNotice(""), 5000); return () => clearTimeout(timer); } }, [notice]);

  function mayLeave() { return !dirty || window.confirm("You have unsaved changes. Discard them?"); }
  function selectNote(note: Note) {
    if (busy || (note.id !== selectedId && !mayLeave())) return;
    if (note.id === selectedId && !draft) return;
    setSelectedId(note.id); setContent(note.content); setDraft(false); setError("");
  }
  function createNote() {
    if (busy || !mayLeave()) return;
    setSelectedId(null); setDraft(true); setContent(""); setError("");
    setTimeout(() => document.getElementById("note-content")?.focus(), 0);
  }
  async function saveNote() {
    if (!content.trim() || busy) return;
    setBusy(true); setError("");
    try {
      const saved = await api<Note>(draft ? "/notes" : `/notes/${selectedId}`, {
        method: draft ? "POST" : "PATCH", body: JSON.stringify({ content }),
      });
      setNotes(previous => draft ? [saved, ...previous] : previous.map(note => note.id === saved.id ? saved : note));
      setSelectedId(saved.id); setContent(saved.content); setDraft(false); setQuery(""); setNotice("Note saved.");
    } catch (err) { handleError(err); }
    finally { setBusy(false); }
  }
  async function deleteNote() {
    setBusy(true); setError("");
    try {
      await api(`/notes/${selectedId}`, { method: "DELETE" });
      const remaining = notes.filter(note => note.id !== selectedId);
      setNotes(remaining); setSelectedId(remaining[0]?.id ?? null); setContent(remaining[0]?.content ?? "");
      setDraft(false); setModal(null); setNotice("Note deleted.");
    } catch (err) { handleError(err); }
    finally { setBusy(false); }
  }
  async function logout() {
    if (busy || !mayLeave()) return;
    setBusy(true); setError("");
    try { await api("/auth/logout", { method: "POST" }); setContent(""); router.replace("/auth"); }
    catch (err) { handleError(err); setBusy(false); }
  }
  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const password = String(data.get("password") || "");
    if (password && !mayLeave()) return;
    setBusy(true); setError("");
    try {
      const updated = await api<User>("/users/me", { method: "PATCH", body: JSON.stringify({
        name: String(data.get("name")).trim(), username: String(data.get("username")).trim(), ...(password ? { password } : {}),
      }) });
      setUser(updated); setModal(null);
      if (password) { setContent(""); router.replace("/auth"); }
      else setNotice("Profile updated.");
    } catch (err) { handleError(err); }
    finally { setBusy(false); }
  }
  async function deleteAccount() {
    setBusy(true); setError("");
    try { await api("/users/me", { method: "DELETE" }); setContent(""); setNotes([]); router.replace("/auth"); }
    catch (err) { handleError(err); setBusy(false); }
  }
  function closeModal() { if (!busy) { setModal(null); setError(""); } }

  if (!user) return <main className="loading-screen"><h1>Notes</h1>{loading ? <p>Loading…</p> : <><p className="error" role="alert">{error || "Unable to load your account."}</p><button onClick={load}>Retry</button></>}</main>;

  return <main className="workspace">
    <header className="app-header">
      <h1>Notes</h1>
      <div className="header-actions"><span>{user.name}</span><button onClick={() => { setError(""); setModal("profile"); }} disabled={busy}>Profile</button><button onClick={logout} disabled={busy}>Log out</button></div>
    </header>
    {error && !modal && <div className="error" role="alert">{error} <button disabled={busy} onClick={() => { if (mayLeave()) void load(); }}>Retry</button></div>}
    {notice && <p className="notice" role="status">{notice}</p>}
    <div className="notes-workspace">
      <NotesList notes={notes} selectedId={selectedId} query={query} loading={loading} onQuery={setQuery} onSelect={selectNote} onCreate={createNote} />
      <section className="editor" aria-label="Note editor">
        <div className="editor-toolbar"><h2>{draft ? "New note" : selected ? "Edit note" : "Note"}</h2><div className="actions">
          {selected && <button className="danger" onClick={() => { setError(""); setModal("delete-note"); }} disabled={busy}>Delete note</button>}
          {editing && <button className="primary" onClick={saveNote} disabled={busy || !content.trim() || (!draft && !dirty)}>{busy ? "Saving…" : "Save note"}</button>}
        </div></div>
        {editing ? <><label className="sr-only" htmlFor="note-content">Note content</label><textarea id="note-content" placeholder="Write a note…" value={content} onChange={event => setContent(event.target.value)} maxLength={100000} disabled={busy} spellCheck /><p className="editor-status">{dirty || draft ? "Unsaved changes" : "Saved"}</p></> : <p className="empty-state">Select a note or create one.</p>}
      </section>
    </div>
    {modal && <Modal title={modal === "profile" ? "Profile" : modal === "delete-note" ? "Delete note?" : "Delete account?"} onClose={closeModal}>
      {error && <p className="error" role="alert">{error}</p>}
      {modal === "profile" ? <><form onSubmit={saveProfile}>
        <label className="field">Name<input name="name" defaultValue={user.name} autoComplete="name" required maxLength={100} disabled={busy} /></label>
        <label className="field">Username<input name="username" defaultValue={user.username} autoComplete="username" required minLength={3} maxLength={50} pattern="[A-Za-z0-9_]+" disabled={busy} /></label>
        <label className="field">New password (optional)<input type="password" name="password" autoComplete="new-password" minLength={8} maxLength={128} disabled={busy} /></label>
        <p className="help">Changing your password signs you out.</p>
        <button className="primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
      </form><div className="danger-zone"><button className="danger" disabled={busy} onClick={() => { setError(""); setModal("delete-account"); }}>Delete account</button></div></> : <>
        <p className="confirmation">{modal === "delete-note" ? `Delete “${noteTitle(content).slice(0, 80)}”? This cannot be undone.` : "Your account and all your notes will be permanently deleted."}</p>
        <div className="actions"><button onClick={closeModal} disabled={busy}>Cancel</button><button className="danger" disabled={busy} onClick={modal === "delete-note" ? deleteNote : deleteAccount}>{busy ? "Deleting…" : modal === "delete-note" ? "Delete note" : "Delete account"}</button></div>
      </>}
    </Modal>}
  </main>;
}
