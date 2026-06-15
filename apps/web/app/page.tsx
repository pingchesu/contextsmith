'use client';

import Link from 'next/link';
import { PageHeader, Card, Metric, StatusChip, EmptyState } from '../components/ui';
import { usePlatform } from '../lib/platform-context';
import { fmt, short } from '../lib/api';

export default function DashboardPage() {
  const { agents, agent, resources, provider, reviewItems, usageItems } = usePlatform();
  const stale = reviewItems.filter((item) => item.freshness_status !== 'fresh').length;
  const hits = usageItems.reduce((sum, item) => sum + item.hit_count, 0);
  return <main className="page">
    <PageHeader eyebrow="Dashboard" title="Agent catalog" description="Enterprise overview of generated knowledge agents, resource health, freshness, and usage." />
    <div className="grid four"><Metric label="Agents" value={agents.length || (agent ? 1 : 0)} /><Metric label="Resources" value={resources.length} /><Metric label="Review risks" value={stale} /><Metric label="Retrieval hits" value={hits} /></div>
    <div className="grid two">
      <Card><h2>Current agent</h2>{agent ? <div className="grid"><p className="muted">{agent.description || 'Generated project agent backed by indexed repo/document resources.'}</p><div className="grid three"><Metric label="Runtime" value={agent.default_runtime} /><Metric label="Snapshots" value={agent.current_snapshot_count} /><Metric label="Graph" value={`${agent.graph_node_count}/${agent.graph_edge_count}`} /></div><div className="code">Last indexed {fmt(agent.last_index_finished_at)} · MCP {agent.mcp_endpoint}</div><Link className="btn" href="/agent-profile">Open agent profile</Link></div> : <EmptyState text="Agent profile is loading." />}</Card>
      <Card><h2>Provider status</h2><div className="grid"><StatusChip value={provider?.status} /><div className="code">{provider ? `${provider.embedding.namespace} · dev_quality=${provider.embedding.dev_quality}` : 'Provider not loaded'}</div><Link className="btn secondary" href="/config">Open configuration</Link></div></Card>
    </div>
    <Card><h2>Available agents</h2>{agents.length === 0 ? <EmptyState text="No agents returned by the API yet." /> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Runtime</th><th>Resources</th><th>Graph</th><th>ID</th></tr></thead><tbody>{agents.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><div className="muted">{item.description || 'No description'}</div></td><td>{item.default_runtime}</td><td>{item.resource_count}</td><td>{item.graph_node_count}/{item.graph_edge_count}</td><td className="code">{short(item.project_id)}</td></tr>)}</tbody></table></div>}</Card>
  </main>;
}
