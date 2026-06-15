'use client';

import { type FormEvent, useState } from 'react';
import { PageHeader, Card, Field, StatusChip, EmptyState } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';
import { fmt, short } from '../../lib/api';

export default function ReviewPage() {
  const { reviewItems, selectedResourceId, selectResource, client, settings, reload, selectedResource } = usePlatform();
  const [status, setStatus] = useState('approved');
  const [note, setNote] = useState('Reviewed from Review Center');
  const [saving, setSaving] = useState(false);
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!selectedResourceId) return;
    setSaving(true);
    try { await client(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources/${selectedResourceId}/review`, { method: 'POST', body: JSON.stringify({ review_status: status, review_note: note, stale_after_days: 30 }) }); await reload(); }
    finally { setSaving(false); }
  }
  return <main className="page">
    <PageHeader eyebrow="Review Center" title="Resource review and drift control" description="Review resources, not opaque IDs: freshness, usage, stale reasons, current snapshot, retrieval state, and whether it should remain approved for agent retrieval." />
    <Card><h2>What is reviewed?</h2><p className="muted">Each row is a source feeding the generated agent. Reviewers decide if the source is current, useful, and safe to keep enabled. Usage count tells whether queries/citations actually depend on it; stale reasons indicate drift risk.</p></Card>
    <div className="grid two"><Card><h2>Review queue</h2>{reviewItems.length === 0 ? <EmptyState text="No review rows loaded." /> : <div className="table-wrap"><table><thead><tr><th>Resource</th><th>Freshness</th><th>Usage</th><th>Index</th><th>Reasons</th></tr></thead><tbody>{reviewItems.map((item) => <tr key={item.resource.id} className={`clickable ${item.resource.id === selectedResourceId ? 'selected' : ''}`} onClick={() => { setStatus(item.resource.review_status); setNote(item.resource.review_note || ''); void selectResource(item.resource.id); }}><td><strong>{item.resource.name}</strong><div className="code">{short(item.resource.current_snapshot_id)}</div></td><td><StatusChip value={item.freshness_status} /><div className="code">age {item.freshness_age_days ?? '—'}d</div></td><td>{item.usage_count}<div className="code">last {fmt(item.last_used_at)}</div></td><td>{item.last_index_status ?? '—'}<div className="code">{fmt(item.last_index_finished_at)}</div></td><td>{item.stale_reasons.join(', ') || 'none'}</td></tr>)}</tbody></table></div>}</Card>
    <Card><h2>Selected review</h2>{!selectedResource ? <EmptyState text="Select a resource to save a review decision." /> : <form className="grid" onSubmit={save}><div><div className="label">Resource</div><strong>{selectedResource.name}</strong><div className="code">{selectedResource.uri}</div></div><Field label="Decision"><select className="input" value={status} onChange={(e) => setStatus(e.target.value)}><option value="approved">approved</option><option value="needs_update">needs_update</option><option value="stale">stale</option><option value="ignored">ignored</option><option value="unreviewed">unreviewed</option></select></Field><Field label="Review note"><textarea className="input" value={note} onChange={(e) => setNote(e.target.value)} /></Field><button className="btn" disabled={saving}>{saving ? 'Saving…' : 'Save review'}</button></form>}</Card></div>
  </main>;
}
