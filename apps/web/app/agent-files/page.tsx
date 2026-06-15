'use client';

import { useEffect, useState } from 'react';
import { PageHeader, Card, EmptyState, Metric, StatusChip } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';
import type { AgentFile, AgentFilesResponse } from '../../lib/types';
import { fmt } from '../../lib/api';

export default function AgentFilesPage() {
  const { settings, client } = usePlatform();
  const [files, setFiles] = useState<AgentFilesResponse | null>(null);
  const [selectedPath, setSelectedPath] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const selected: AgentFile | null = files?.files.find((file) => file.path === selectedPath) ?? files?.files[0] ?? null;

  async function load(regenerate = false) {
    setBusy(true); setError(null);
    try {
      const result = await client<AgentFilesResponse>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/agent-files${regenerate ? '/regenerate' : ''}`, { method: regenerate ? 'POST' : 'GET' });
      setFiles(result);
      setSelectedPath((previous) => result.files.some((file) => file.path === previous) ? previous : result.files[0]?.path ?? '');
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  useEffect(() => { void load(false); }, [settings.workspaceId, settings.projectId]);

  return <main className="page">
    <PageHeader eyebrow="Agent Files" title="Generated agent files and skills" description="Generate the files that make the project/repo agents concrete: manifest, AGENTS.md, project skill, repo skills, and env template. These files are generated from imported resources and current snapshots." actions={<button className="btn" disabled={busy} onClick={() => void load(true)}>{busy ? 'Regenerating…' : 'Regenerate agent files'}</button>} />
    {error ? <div className="notice error">{error}</div> : null}
    <div className="grid four"><Metric label="Files" value={files?.files.length ?? 0} /><Metric label="Resources" value={files?.resource_count ?? 0} /><Metric label="Repo skills" value={files?.repo_agent_count ?? 0} /><Metric label="Generated" value={fmt(files?.generated_at)} /></div>
    <div className="grid two">
      <Card>
        <h2>Generated files</h2>
        {!files ? <EmptyState text="Agent files are loading." /> : <div className="grid">{files.files.map((file) => <button type="button" key={file.path} className={`scope-pill ${selected?.path === file.path ? 'active' : ''}`} onClick={() => setSelectedPath(file.path)}><strong>{file.path}</strong><small>{file.kind} · {file.description}</small></button>)}</div>}
      </Card>
      <Card>
        <h2>{selected?.path ?? 'Preview'}</h2>
        {selected ? <div className="grid"><StatusChip value={selected.kind} /><p className="muted">{selected.description}</p><pre className="code-block light">{selected.content}</pre></div> : <EmptyState text="Select a generated file." />}
      </Card>
    </div>
  </main>;
}
