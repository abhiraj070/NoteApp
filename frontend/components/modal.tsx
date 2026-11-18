"use client";

import { useEffect, useRef } from "react";

export function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} className="modal" aria-labelledby="modal-title" onCancel={event => { event.preventDefault(); onClose(); }}>
    <div className="modal-heading"><h2 id="modal-title">{title}</h2><button aria-label="Close dialog" onClick={onClose}>Close</button></div>
    {children}
  </dialog>;
}
