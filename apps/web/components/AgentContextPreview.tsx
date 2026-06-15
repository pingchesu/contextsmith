'use client';

import type { AgentContextResponse, Resource } from '../lib/types';
import { short } from '../lib/api';
import { Card, EmptyState, Metric } from './ui';

export function AgentContextPreview({ result, resources, title = 'Generated context packet' }: { result: AgentContextResponse | null; resources: Resource[]; title?: string }) {
  if (!result) return <EmptyState text="No generated runtime context yet. Generate a preview to review the agent output, instruction, citations, and code symbols." />;
  const byResource = new Map(resources.map((resource) => [resource.id, resource]));
  const citedResources = new Set(result.citations.map((citation) => citation.resource_id));
  return <div className="grid">
    <div className="grid four"><Metric label="Runtime" value={result.runtime} /><Metric label="Citations" value={result.citations.length} /><Metric label="Cited resources" value={citedResources.size} /><Metric label="Symbols" value={result.symbols?.length ?? 0} /></div>
    <Card><h2>Instruction the agent receives</h2><p className="muted">This is the generated runtime instruction. Review whether it preserves read-only/approval boundaries and matches the target runtime.</p><pre className="code-block light">{result.instruction}</pre></Card>
    <Card><h2>{title}</h2><p className="muted">This is the actual context packet a runtime agent would read. If this looks wrong/noisy/stale, the repo agent is not review-ready.</p><pre className="code-block">{result.context || 'No context returned for this query/scope.'}</pre></Card>
    <Card><h2>Citations and evidence</h2>{result.citations.length === 0 ? <EmptyState text="No citations returned. This is a retrieval failure for this query/scope." /> : <div className="table-wrap"><table><thead><tr><th>Resource</th><th>Path/title</th><th>Score</th><th>Version</th></tr></thead><tbody>{result.citations.map((citation) => { const resource = byResource.get(citation.resource_id); return <tr key={citation.chunk_id}><td><strong>{resource?.name ?? short(citation.resource_id)}</strong><div className="code">resource {short(citation.resource_id)}</div></td><td><strong>{citation.title || citation.path || short(citation.chunk_id)}</strong><div className="code">chunk {short(citation.chunk_id)} · ordinal {citation.ordinal}</div></td><td>{citation.score.toFixed(3)}<div className="code">graph {citation.graph_score.toFixed(3)}</div></td><td className="code">{citation.version_kind}={short(citation.version)}{citation.commit ? ` · ${short(citation.commit)}` : ''}</td></tr>; })}</tbody></table></div>}</Card>
    <Card><h2>Code symbols</h2>{!result.symbols || result.symbols.length === 0 ? <EmptyState text="No code symbols were returned for this query/scope." /> : <div className="table-wrap"><table><thead><tr><th>Symbol</th><th>Path</th><th>Lines</th><th>Score</th></tr></thead><tbody>{result.symbols.slice(0, 20).map((symbol) => <tr key={`${symbol.resource_id}-${symbol.path}-${symbol.name}-${symbol.line_start}`}><td><strong>{symbol.name}</strong><div className="code">{symbol.kind} · {symbol.language}</div></td><td className="code">{symbol.path}</td><td>{symbol.line_start}-{symbol.line_end}</td><td>{symbol.score.toFixed(3)}</td></tr>)}</tbody></table></div>}</Card>
  </div>;
}
