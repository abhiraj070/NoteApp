export type User = { id: number; name: string; username: string };
export type Note = { id: number; content: string; user_id: number };

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

let refreshing: Promise<boolean> | null = null;

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options, credentials: "include", cache: "no-store",
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }
  if (response.status === 401 && retry && !path.startsWith("/auth/")) {
    if (!refreshing) {
      refreshing = fetch("/api/auth/refresh", { method: "POST", credentials: "include" })
        .then(result => result.ok).catch(() => false).finally(() => { refreshing = null; });
    }
    if (await refreshing) return api<T>(path, options, false);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    let message = "Something went wrong. Please try again.";
    if (typeof body?.detail === "string") message = body.detail;
    else if (Array.isArray(body?.detail)) {
      message = body.detail.map((item: { loc?: string[]; msg?: string }) =>
        `${item.loc?.slice(1).join(".") || "Input"}: ${item.msg || "Invalid value"}`).join(". ");
    } else if (response.status === 502 || response.status === 503) message = "The notes server is unavailable. Please try again shortly.";
    throw new ApiError(message, response.status);
  }
  return response.status === 204 ? undefined as T : response.json();
}

export async function allNotes(): Promise<Note[]> {
  const notes: Note[] = [];
  for (let offset = 0; ; offset += 100) {
    const batch = await api<Note[]>(`/notes?offset=${offset}&limit=100`);
    notes.push(...batch);
    if (batch.length < 100) return notes;
  }
}

export function noteTitle(content: string) {
  return content.split("\n").find(line => line.trim())?.trim() || "Untitled note";
}
