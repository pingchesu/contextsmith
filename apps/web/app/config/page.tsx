'use client';

import { type FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { PageHeader, Card, Field } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';

export default function ConfigPage() {
  const { settings, workspaces, projectsByWorkspace, workspace, project, reload, chooseScope } = usePlatform();
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(settings.workspaceId);
  const [selectedProjectId, setSelectedProjectId] = useState(settings.projectId);
  const availableProjects = useMemo(() => projectsByWorkspace[selectedWorkspaceId] ?? [], [projectsByWorkspace, selectedWorkspaceId]);

  useEffect(() => { setSelectedWorkspaceId(settings.workspaceId); setSelectedProjectId(settings.projectId); }, [settings.workspaceId, settings.projectId]);
  useEffect(() => {
    if (!availableProjects.some((item) => item.id === selectedProjectId)) setSelectedProjectId(availableProjects[0]?.id ?? '');
  }, [availableProjects, selectedProjectId]);

  async function saveScope(event: FormEvent) {
    event.preventDefault();
    const next = chooseScope(selectedWorkspaceId, selectedProjectId);
    await reload(next);
  }

  return <main className="page"><PageHeader eyebrow="Settings" title="Workspace settings" description="Choose the active workspace/project. Source lifecycle work belongs in Sources so create, index, inspect, and ask actions stay on one canonical path." />
    <div className="grid two"><Card><h2>Workspace and project</h2><p className="muted">Pick the active workspace and project by name.</p><form className="grid" onSubmit={saveScope}><Field label="Workspace"><select className="input" value={selectedWorkspaceId} onChange={(event) => setSelectedWorkspaceId(event.target.value)}>{workspaces.length === 0 ? <option value={settings.workspaceId}>{workspace?.name ?? 'No workspace loaded'}</option> : workspaces.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Project"><select className="input" value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>{availableProjects.length === 0 ? <option value={settings.projectId}>{project?.name ?? 'No project loaded'}</option> : availableProjects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><button type="submit" className="btn" disabled={!selectedWorkspaceId || !selectedProjectId}>Save workspace</button></form></Card>
    <Card><h2>Source lifecycle moved to Sources</h2><p className="muted">Settings no longer exposes a second Add source form. Use Sources as the canonical hub for connecting, indexing, previewing, and asking cited questions over sources.</p><div className="notice"><strong>Canonical path</strong><div className="muted">Sources → Connect source → Index activity → Preview this source / Ask in Workbench</div></div><div className="toolbar" style={{ marginTop: 12 }}><Link className="btn" href="/sources">Open Sources</Link><Link className="btn secondary" href="/workbench">Open Workbench</Link></div></Card></div>
  </main>;
}
