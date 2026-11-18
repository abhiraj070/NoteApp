"use client";

import { Note, noteTitle } from "@/lib/api";

type Props = {
  notes: Note[]; selectedId: number | null; query: string; loading: boolean;
  onQuery: (value: string) => void; onSelect: (note: Note) => void; onCreate: () => void;
};

export function NotesList({ notes, selectedId, query, loading, onQuery, onSelect, onCreate }: Props) {
  const visible = notes.filter(note => note.content.toLowerCase().includes(query.toLowerCase()));
  return <section className="notes-column" aria-label="Your notes">
    <div className="list-heading"><h2>My notes ({notes.length})</h2><button onClick={onCreate} disabled={loading}>New note</button></div>
    <input className="search" aria-label="Search your notes" placeholder="Search notes" value={query} onChange={event => onQuery(event.target.value)} />
    <div className="note-items" aria-busy={loading}>
      {loading ? <p className="empty-state">Loading…</p> : visible.length ? visible.map(note => <button key={note.id} className={`note-item ${note.id === selectedId ? "selected" : ""}`} onClick={() => onSelect(note)} aria-pressed={note.id === selectedId}>
        <strong>{noteTitle(note.content)}</strong>
        <span>{note.content.split("\n").slice(1).join(" ").trim().slice(0, 100)}</span>
      </button>) : <p className="empty-state">{query ? "No matching notes." : "No notes yet."}</p>}
    </div>
  </section>;
}
