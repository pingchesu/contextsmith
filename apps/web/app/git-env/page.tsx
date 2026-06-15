'use client';

import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { PageHeader, Card, EmptyState, Field, Metric } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';
import type { GitResourceEnv } from '../../lib/types';
import { fmt, short } from '../../lib/api';

type Draft = { branch: string; auth_token_env: string; clone_timeout: string; max_file_bytes: string; max_repo_files: string; max_repo_bytes: string; update_frequency: string };

function toDraft(env: GitResourceEnv | null): Draft {
  return {
    branch: env?.branch ?? '',
    auth_token_env: env?.auth_token_env ?? '',
    clone_timeout: env?.clone_timeout?.toString() ?? '',
    max_file_bytes: env?.max_file_bytes?.toString() ?? '',
    max_repo_files: env?.max_repo_files?.toString() ?? '',
    max_repo_bytes: env?.max_repo_bytes?.toString() ?? '',
    update_frequency: env?.update_frequency ?? 'daily',
  };
}

function optionalNumber(value: string) { return value.trim() ? Number(value.trim()) : null; }

export default function GitEnvPage() {
  const { settings, client, reload } = usePlatform();
  const [items, setItems] = useState<GitResourceEnv[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const selected = useMemo(() => items.find((item) => item.resource_id === selectedId) ?? items[0] ?? null, [items, selectedId]);
  const [draft, setDraft] = useState<Draft>(toDraft(null));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true); setError(null);
    try {
      const next = await client<GitResourceEnv[]>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/git-env`);
      setItems(next);
      const current = next.find((item) => item.resource_id === selectedId) ?? next[0] ?? null;
      setSelectedId(current?.resource_id ?? '');
      setDraft(toDraft(current));
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  useEffect(() => { void load(); }, [settings.workspaceId, settings.projectId]);

  function choose(id: string) {
    setSelectedId(id);
    setDraft(toDraft(items.find((item) => item.resource_id === id) ?? null));
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setBusy(true); setError(null);
    try {
      await client<GitResourceEnv>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources/${selected.resource_id}/git-env`, {
        method: 'PATCH',
        body: JSON.stringify({
          branch: draft.branch.trim() || null,
          auth_token_env: draft.auth_token_env.trim() || null,
          clone_timeout: optionalNumber(draft.clone_timeout),
          max_file_bytes: optionalNumber(draft.max_file_bytes),
          max_repo_files: optionalNumber(draft.max_repo_files),
          max_repo_bytes: optionalNumber(draft.max_repo_bytes),
          update_frequency: draft.update_frequency,
        }),
      });
      await reload();
      await load();
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  return <main className="page">
    <PageHeader eyebrow="Git Env" title="Git import environment" description="Configure repo import/refetch behavior without storing secrets. Store only an environment variable name such as GITHUB_TOKEN_FOR_CONTEXTSMITH; the worker reads the token from its own environment at clone time." actions={<button className="btn secondary" disabled={busy} onClick={() => void load()}>{busy ? 'Loading…' : 'Reload'}</button>} />
    {error ? <div className="notice error">{error}</div> : null}
    <div className="grid four"><Metric label="Git resources" value={items.length} /><Metric label="Selected" value={selected?.name ?? '—'} /><Metric label="Next refresh" value={fmt(selected?.next_refresh_at)} /><Metric label="Resource ID" value={short(selected?.resource_id)} /></div>
    <div className="grid two">
      <Card><h2>Repos</h2>{items.length === 0 ? <EmptyState text="No git resources imported yet. Use Import Resources first." /> : <div className="grid">{items.map((item) => <button key={item.resource_id} type="button" className={`scope-pill ${selected?.resource_id === item.resource_id ? 'active' : ''}`} onClick={() => choose(item.resource_id)}><strong>{item.name}</strong><small>{item.uri} · branch {item.branch ?? 'default'} · refresh {item.update_frequency}</small></button>)}</div>}</Card>
      <Card><h2>Selected git env</h2>{!selected ? <EmptyState text="Select a git resource." /> : <form className="grid" onSubmit={save}><Field label="Branch/ref"><input className="input" value={draft.branch} onChange={(event) => setDraft({ ...draft, branch: event.target.value })} /></Field><Field label="Auth token env var"><input className="input" placeholder="GITHUB_TOKEN_FOR_CONTEXTSMITH" value={draft.auth_token_env} onChange={(event) => setDraft({ ...draft, auth_token_env: event.target.value })} /></Field><div className="grid two"><Field label="Clone timeout seconds"><input className="input" value={draft.clone_timeout} onChange={(event) => setDraft({ ...draft, clone_timeout: event.target.value })} /></Field><Field label="Update frequency"><select className="input" value={draft.update_frequency} onChange={(event) => setDraft({ ...draft, update_frequency: event.target.value })}><option value="manual">manual</option><option value="hourly">hourly</option><option value="daily">daily</option><option value="weekly">weekly</option></select></Field></div><div className="grid three"><Field label="Max file bytes"><input className="input" value={draft.max_file_bytes} onChange={(event) => setDraft({ ...draft, max_file_bytes: event.target.value })} /></Field><Field label="Max repo files"><input className="input" value={draft.max_repo_files} onChange={(event) => setDraft({ ...draft, max_repo_files: event.target.value })} /></Field><Field label="Max repo bytes"><input className="input" value={draft.max_repo_bytes} onChange={(event) => setDraft({ ...draft, max_repo_bytes: event.target.value })} /></Field></div><button className="btn" disabled={busy}>Save git env</button><div className="notice">Secrets are not stored in ContextSmith. Put the token in the worker container env, then reference the env var name here.</div></form>}</Card>
    </div>
  </main>;
}
