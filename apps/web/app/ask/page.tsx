'use client';

import { useState } from 'react';
import { PageHeader, Card, StatusChip } from '../../components/ui';
import { AgentContextPreview } from '../../components/AgentContextPreview';
import { ResourceScopePicker, describeScope } from '../../components/ResourceScopePicker';
import { usePlatform } from '../../lib/platform-context';
import type { AgentContextResponse } from '../../lib/types';

export default function AskPage() {
  const { settings, client, resources, agent } = usePlatform();
  const [question, setQuestion] = useState('In AngiBrain only: how does device-config/store.yaml get applied or rendered into runtime configuration? Include exact files and cited context.');
  const [runtime, setRuntime] = useState(agent?.default_runtime ?? 'hermes');
  const [scopeResourceIds, setScopeResourceIds] = useState<string[]>([]);
  const [topK, setTopK] = useState(8);
  const [result, setResult] = useState<AgentContextResponse | null>(null);
  const [generatedFor, setGeneratedFor] = useState<{ scope: string; question: string; runtime: string; topK: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  async function ask() {
    setLoading(true); setError(null);
    try {
      const nextResult = await client<AgentContextResponse>(`/workspaces/${settings.workspaceId}/projects/${settings.projectId}/agent-context`, {
        method: 'POST',
        body: JSON.stringify({ query: question, runtime, resource_ids: scopeResourceIds.length ? scopeResourceIds : null, top_k: topK, max_chars: 22000, include_code_symbols: true }),
      });
      setResult(nextResult);
      setGeneratedFor({ scope: describeScope(resources, scopeResourceIds), question, runtime, topK });
    } catch (err) { setError(String(err)); }
    finally { setLoading(false); }
  }
  return <main className="page"><PageHeader eyebrow="Ask / Citations" title="Query the generated agent" description="Ask is independent from Review Center selection. Choose the scope here: all resources, one repo, or multiple repos/docs. Then inspect the exact context packet, citations, and symbols returned to the runtime." />
    <Card><div className="grid"><div className="grid three"><label><span className="label">Runtime</span><select className="input" value={runtime} onChange={(e) => setRuntime(e.target.value)}><option value="hermes">Hermes</option><option value="claude">Claude</option><option value="codex">Codex</option><option value="cursor">Cursor</option><option value="api">API</option></select></label><label><span className="label">Top K</span><input className="input" type="number" min={1} max={50} value={topK} onChange={(e) => setTopK(Number(e.target.value))} /></label><div><div className="label">Current scope</div><div>{describeScope(resources, scopeResourceIds)}</div></div></div><ResourceScopePicker resources={resources} selectedIds={scopeResourceIds} onChange={setScopeResourceIds} label="Ask scope" /><label><span className="label">Question</span><textarea className="input" style={{ minHeight: 90 }} value={question} onChange={(e) => setQuestion(e.target.value)} /></label><div className="toolbar"><button type="button" className="btn" disabled={loading} onClick={() => void ask()}>{loading ? 'Generating…' : 'Generate cited answer context'}</button><StatusChip value={result ? 'generated' : 'idle'} /></div></div>{error ? <div className="notice error">{error}</div> : null}</Card>
    {generatedFor ? <div className="notice">Generated for: <strong>{generatedFor.scope}</strong> · {generatedFor.runtime} · topK {generatedFor.topK}<br /><span className="muted">{generatedFor.question}</span></div> : null}
    {generatedFor && (generatedFor.scope !== describeScope(resources, scopeResourceIds) || generatedFor.question !== question || generatedFor.runtime !== runtime || generatedFor.topK !== topK) ? <div className="notice error">Displayed context was generated for previous controls. Regenerate before review/approval.</div> : null}
    <AgentContextPreview result={result} resources={resources} />
  </main>;
}
