'use client';

import { type FormEvent, useState } from 'react';
import { PageHeader, Card, Field, Metric, StatusChip } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';
import type { IndexRun, Resource } from '../../lib/types';
import { short } from '../../lib/api';

type ResourceType = 'git' | 'url' | 'markdown' | 'upload';

function defaultUri(type: ResourceType) {
  if (type === 'git') return 'https://github.com/owner/repo.git';
  if (type === 'url') return 'https://example.com/docs';
  if (type === 'markdown') return 'doc://runbook.md';
  return 'upload://notes.txt';
}

export default function ImportResourcesPage() {
  const { settings, client, reload, resources } = usePlatform();
  const [type, setType] = useState<ResourceType>('git');
  const [name, setName] = useState('New Repo Agent');
  const [uri, setUri] = useState(defaultUri('git'));
  const [branch, setBranch] = useState('main');
  const [authTokenEnv, setAuthTokenEnv] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [content, setContent] = useState('');
  const [filename, setFilename] = useState('notes.txt');
  const [refreshNow, setRefreshNow] = useState(true);
  const [created, setCreated] = useState<Resource | null>(null);
  const [run, setRun] = useState<IndexRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function changeType(next: ResourceType) {
    setType(next);
    setUri(defaultUri(next));
    setName(next === 'git' ? 'New Repo Agent' : next === 'url' ? 'New URL Resource' : next === 'markdown' ? 'New Markdown Resource' : 'New Upload Resource');
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(null); setRun(null); setCreated(null);
    try {
      const source_config = type === 'git'
        ? { url: uri, branch, ...(authTokenEnv.trim() ? { auth_token_env: authTokenEnv.trim() } : {}) }
        : type === 'url'
          ? { url: uri }
          : type === 'upload'
            ? { content, filename, content_type: 'text/plain' }
            : { content, path: uri, title: name };
      const resource = await client<Resource>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources`, {
        method: 'POST',
        body: JSON.stringify({ type, name, uri, update_frequency: frequency, source_config }),
      });
      setCreated(resource);
      if (refreshNow) {
        setRun(await client<IndexRun>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources/${resource.id}/refresh`, { method: 'POST' }));
      }
      await reload();
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  return <main className="page">
    <PageHeader eyebrow="Import" title="Import repos and resources" description="Add git repos, URLs, markdown, or uploaded text as resources. Git repos become repo-agent candidates; refresh/index builds snapshots, chunks, symbols, graph, and runtime context." />
    <div className="grid four"><Metric label="Resources" value={resources.length} /><Metric label="Git repos" value={resources.filter((resource) => resource.type === 'git').length} /><Metric label="Refresh mode" value={refreshNow ? 'index now' : 'create only'} /><Metric label="Project" value={short(settings.projectId)} /></div>
    <div className="grid two">
      <Card>
        <h2>Add resource</h2>
        <form className="grid" onSubmit={submit}>
          <Field label="Resource type"><select className="input" value={type} onChange={(event) => changeType(event.target.value as ResourceType)}><option value="git">Git repo → repo agent</option><option value="url">URL / web page</option><option value="markdown">Markdown / inline doc</option><option value="upload">Upload text</option></select></Field>
          <Field label="Name"><input className="input" value={name} onChange={(event) => setName(event.target.value)} /></Field>
          <Field label={type === 'git' ? 'Git URL' : 'URI / URL'}><input className="input" value={uri} onChange={(event) => setUri(event.target.value)} /></Field>
          {type === 'git' ? <div className="grid two"><Field label="Branch/ref"><input className="input" value={branch} onChange={(event) => setBranch(event.target.value)} /></Field><Field label="Auth token env var"><input className="input" placeholder="GITHUB_TOKEN_FOR_CONTEXTSMITH" value={authTokenEnv} onChange={(event) => setAuthTokenEnv(event.target.value)} /></Field></div> : null}
          {type === 'upload' ? <Field label="Filename"><input className="input" value={filename} onChange={(event) => setFilename(event.target.value)} /></Field> : null}
          {type === 'markdown' || type === 'upload' ? <Field label="Content"><textarea className="input" rows={10} value={content} onChange={(event) => setContent(event.target.value)} /></Field> : null}
          <div className="grid two"><Field label="Update frequency"><select className="input" value={frequency} onChange={(event) => setFrequency(event.target.value)}><option value="manual">manual</option><option value="hourly">hourly</option><option value="daily">daily</option><option value="weekly">weekly</option></select></Field><label className="scope-pill active"><input type="checkbox" checked={refreshNow} onChange={(event) => setRefreshNow(event.target.checked)} /> Create index immediately</label></div>
          <button className="btn" disabled={busy}>{busy ? 'Importing…' : 'Import resource'}</button>
        </form>
      </Card>
      <Card>
        <h2>Import result</h2>
        {error ? <div className="notice error">{error}</div> : null}
        {created ? <div className="grid"><StatusChip value={created.status} /><div className="code">resource_id={created.id}<br />type={created.type}<br />snapshot={created.current_snapshot_id ?? 'pending'}</div>{run ? <div className="notice">Index job queued: <span className="code">{run.id}</span>. Use Update / Reindex to monitor and rerun.</div> : <div className="notice">Resource created. Indexing was not started.</div>}</div> : <div className="empty">No import submitted yet.</div>}
        <div className="notice">For private git, put the token on the worker environment and enter only the env var name here. ContextSmith stores `auth_token_env`, not the token value.</div>
      </Card>
    </div>
  </main>;
}
