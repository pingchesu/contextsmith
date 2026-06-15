'use client';

import { useMemo, useState } from 'react';
import { PageHeader, Card, EmptyState, Field, Metric, StatusChip } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';
import type { AgentFilesResponse, DueRefreshResponse, IndexRun } from '../../lib/types';
import { fmt, short } from '../../lib/api';

export default function MaintenancePage() {
  const { resources, settings, client, reload, indexRuns, selectResource, selectedResourceId } = usePlatform();
  const activeResources = useMemo(() => resources.filter((resource) => resource.status === 'active'), [resources]);
  const [selectedId, setSelectedId] = useState(selectedResourceId || activeResources[0]?.id || '');
  const [result, setResult] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const selected = activeResources.find((resource) => resource.id === selectedId) ?? activeResources[0] ?? null;

  async function refreshSelected() {
    if (!selected) return;
    setBusy(true); setResult('');
    try {
      const run = await client<IndexRun>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources/${selected.id}/refresh`, { method: 'POST' });
      await selectResource(selected.id);
      await reload();
      setResult(`Queued reindex for ${selected.name}: ${run.id}`);
    } catch (err) { setResult(String(err)); }
    finally { setBusy(false); }
  }

  async function runDue(dryRun: boolean) {
    setBusy(true); setResult('');
    try {
      const due = await client<DueRefreshResponse>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/scheduled-refreshes?dry_run=${dryRun ? 'true' : 'false'}&limit=100`, { method: 'POST' });
      await reload();
      setResult(`${dryRun ? 'Due refresh preview' : 'Scheduled refresh enqueue'}: scanned=${due.scanned}, enqueued=${due.enqueued}, resources=${due.resource_ids.join(', ') || 'none'}`);
    } catch (err) { setResult(String(err)); }
    finally { setBusy(false); }
  }

  async function regenerateAgentFiles() {
    setBusy(true); setResult('');
    try {
      const files = await client<AgentFilesResponse>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/agent-files/regenerate`, { method: 'POST' });
      setResult(`Regenerated ${files.files.length} agent file(s), including ${files.repo_agent_count} repo skill(s).`);
    } catch (err) { setResult(String(err)); }
    finally { setBusy(false); }
  }

  return <main className="page">
    <PageHeader eyebrow="Maintenance" title="Update repos, reindex, regenerate agent" description="Operational controls for drift: update a selected resource/repo, run due scheduled refreshes, and regenerate generated agent files/skills after resources change." />
    <div className="grid four"><Metric label="Active resources" value={activeResources.length} /><Metric label="Git repos" value={activeResources.filter((resource) => resource.type === 'git').length} /><Metric label="Selected" value={selected?.name ?? '—'} /><Metric label="Recent runs" value={indexRuns.length} /></div>
    <div className="grid two">
      <Card>
        <h2>Resource update / reindex</h2>
        {activeResources.length === 0 ? <EmptyState text="No active resources to update." /> : <div className="grid"><Field label="Resource"><select className="input" value={selected?.id ?? ''} onChange={(event) => setSelectedId(event.target.value)}>{activeResources.map((resource) => <option key={resource.id} value={resource.id}>{resource.name} — {resource.type} · {short(resource.current_snapshot_id)}</option>)}</select></Field><div className="code">uri={selected?.uri}<br />next_refresh={fmt(selected?.next_refresh_at)}<br />last_refresh={fmt(selected?.last_refresh_finished_at)}</div><button className="btn" disabled={busy || !selected} onClick={refreshSelected}>{busy ? 'Working…' : selected?.type === 'git' ? 'Update repo and reindex' : 'Reindex resource'}</button></div>}
      </Card>
      <Card>
        <h2>Project maintenance</h2>
        <div className="grid"><button className="btn secondary" disabled={busy} onClick={() => void runDue(true)}>Preview due scheduled refreshes</button><button className="btn" disabled={busy} onClick={() => void runDue(false)}>Run due scheduled refreshes</button><button className="btn" disabled={busy} onClick={regenerateAgentFiles}>Regenerate agent files / skills</button><div className="notice">Regenerate does not write into source repos. It produces centralized ContextSmith agent files derived from imported resources.</div></div>
      </Card>
      <Card><h2>Selected index runs</h2>{indexRuns.length === 0 ? <EmptyState text="Select a resource or run a reindex to see index runs." /> : <div className="table-wrap"><table><thead><tr><th>Status</th><th>Trigger</th><th>Chunks</th><th>Symbols</th><th>Finished</th></tr></thead><tbody>{indexRuns.slice(0, 10).map((run) => <tr key={run.id}><td><StatusChip value={run.status} /></td><td>{run.trigger}</td><td>{run.chunks_created}</td><td>{run.symbols_created}</td><td>{fmt(run.finished_at)}</td></tr>)}</tbody></table></div>}</Card>
      <Card><h2>Result</h2>{result ? <pre className="code-block light">{result}</pre> : <EmptyState text="No maintenance action run yet." />}</Card>
    </div>
  </main>;
}
