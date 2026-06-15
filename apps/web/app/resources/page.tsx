'use client';

import { useState } from 'react';
import { PageHeader, Card, Metric, StatusChip, EmptyState } from '../../components/ui';
import { AgentContextPreview } from '../../components/AgentContextPreview';
import { usePlatform } from '../../lib/platform-context';
import type { AgentContextResponse } from '../../lib/types';
import { fmt, short } from '../../lib/api';

export default function ResourcesPage() {
  const { resources, selectedResource, selectedResourceId, selectResource, snapshots, indexRuns, graph, loading, client, settings, reload, agent } = usePlatform();
  const [refreshing, setRefreshing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [preview, setPreview] = useState<AgentContextResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  async function refreshSelected() {
    if (!selectedResource) return;
    setRefreshing(true);
    try { await client(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/resources/${selectedResource.id}/refresh`, { method: 'POST' }); await reload(); }
    finally { setRefreshing(false); }
  }
  async function previewSelected() {
    if (!selectedResource) return;
    setGenerating(true); setPreviewError(null);
    try {
      setPreview(await client<AgentContextResponse>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/agent-context`, {
        method: 'POST',
        body: JSON.stringify({ query: `Summarize what ${selectedResource.name} contributes to this generated repo agent. Include important files, concepts, operational boundaries, and what a human reviewer should inspect. Cite exact context.`, runtime: agent?.default_runtime ?? 'hermes', resource_ids: [selectedResource.id], top_k: 10, max_chars: 18000, include_code_symbols: true }),
      }));
    } catch (err) { setPreviewError(String(err)); }
    finally { setGenerating(false); }
  }
  return <main className="page">
    <PageHeader eyebrow="Resources" title="Resource inventory and generated evidence" description="Repo/document resources that feed the generated agent. Select a row to inspect snapshots, index runs, graph coverage, and the generated context this resource contributes to the agent." actions={<><button className="btn secondary" disabled={!selectedResource || generating} onClick={previewSelected}>{generating ? 'Generating…' : 'Preview resource content'}</button><button className="btn" disabled={!selectedResource || refreshing || loading} onClick={refreshSelected}>{refreshing ? 'Refreshing…' : 'Refresh selected'}</button></>} />
    <div className="grid two"><Card><h2>Resources</h2>{resources.length === 0 ? <EmptyState text="No resources loaded." /> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Status</th><th>Review</th><th>Update</th><th>Snapshot</th></tr></thead><tbody>{resources.map((resource) => <tr key={resource.id} className={`clickable ${resource.id === selectedResourceId ? 'selected' : ''}`} onClick={() => { setPreview(null); void selectResource(resource.id); }}><td><strong>{resource.name}</strong><div className="code">{resource.type} · {short(resource.id)}</div></td><td><StatusChip value={resource.status} /><div className="code">retrieval {resource.retrieval_enabled ? 'on' : 'off'}</div></td><td><StatusChip value={resource.review_status} /></td><td>{resource.update_frequency}<div className="code">next {fmt(resource.next_refresh_at)}</div></td><td className="code">{short(resource.current_snapshot_id)}</td></tr>)}</tbody></table></div>}</Card>
    <Card><h2>Selected resource evidence</h2>{!selectedResource ? <EmptyState text="Select a resource to review its generated evidence." /> : <div className="grid"><div className="grid three"><Metric label="Status" value={selectedResource.status} /><Metric label="Review" value={selectedResource.review_status} /><Metric label="Graph preview" value={graph ? `${graph.node_count}/${graph.edge_count}` : '—'} /></div><div><div className="label">URI</div><div className="code">{selectedResource.uri}</div></div><div><div className="label">Current snapshot</div><div className="code">{short(selectedResource.current_snapshot_id)}</div></div><div><div className="label">Last refresh</div><div className="code">{fmt(selectedResource.last_refresh_finished_at)}</div></div></div>}</Card></div>
    <div className="grid two"><Card><h2>Snapshots</h2>{snapshots.length === 0 ? <EmptyState text="No snapshots loaded." /> : <div className="table-wrap"><table><thead><tr><th>Status</th><th>Version</th><th>Indexed</th></tr></thead><tbody>{snapshots.map((s) => <tr key={s.id}><td>{s.is_current ? <StatusChip value="current" /> : <StatusChip value={s.status} />}</td><td className="code">{s.version_kind}={short(s.version)}</td><td>{fmt(s.indexed_at)}</td></tr>)}</tbody></table></div>}</Card><Card><h2>Index runs</h2>{indexRuns.length === 0 ? <EmptyState text="No index runs loaded." /> : <div className="table-wrap"><table><thead><tr><th>Status</th><th>Chunks</th><th>Symbols</th><th>Finished</th></tr></thead><tbody>{indexRuns.slice(0, 8).map((run) => <tr key={run.id}><td><StatusChip value={run.status} /></td><td>{run.chunks_created}</td><td>{run.symbols_created}</td><td>{fmt(run.finished_at)}</td></tr>)}</tbody></table></div>}</Card></div>
    {previewError ? <div className="notice error">{previewError}</div> : null}
    <AgentContextPreview result={preview} resources={resources} title="Selected resource contribution to agent" />
  </main>;
}
