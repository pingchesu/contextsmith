import type { ReactNode } from 'react';

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description ? <p className="muted">{description}</p> : null}</div>{actions ? <div className="toolbar">{actions}</div> : null}</div>;
}
export function Card({ children }: { children: ReactNode }) { return <section className="card">{children}</section>; }
export function Metric({ label, value }: { label: string; value: ReactNode }) { return <div className="metric"><div className="metric-label">{label}</div><div className="metric-value">{value}</div></div>; }
export function StatusChip({ value }: { value?: string | null }) { const v = value ?? 'unknown'; const cls = v.includes('active') || v.includes('ok') || v.includes('approved') || v.includes('succeeded') ? 'ok' : v.includes('fail') || v.includes('stale') ? 'bad' : 'warn'; return <span className={`chip ${cls}`}>{v}</span>; }
export function EmptyState({ text }: { text: string }) { return <div className="empty">{text}</div>; }
export function Field({ label, children }: { label: string; children: ReactNode }) { return <label><span className="label">{label}</span>{children}</label>; }
