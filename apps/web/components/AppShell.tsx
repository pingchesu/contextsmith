'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { usePlatform } from '../lib/platform-context';
import { short } from '../lib/api';

const NAV = [
  ['/', 'Dashboard'],
  ['/agent-profile', 'Agent Profile'],
  ['/resources', 'Resources'],
  ['/review', 'Review Center'],
  ['/ask', 'Ask / Citations'],
  ['/config', 'Config'],
  ['/users', 'User Management'],
  ['/admin', 'Admin'],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { agent, provider, workspace, project, settings, loading, error, reload } = usePlatform();
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-kicker">CONTEXTSMITH</div><div className="brand-title">Knowledge Agents</div></div>
      <nav className="nav-group">{NAV.map(([href, label]) => <Link key={href} href={href} className={`nav-link ${pathname === href ? 'active' : ''}`}><span>{label}</span></Link>)}</nav>
      <div className="sidebar-footer"><strong>{agent?.name ?? 'AngiKnowledge Agent'}</strong><br />{workspace?.name ?? 'Workspace'}<br />{project?.name ?? 'Project'}<br /><span className="code">{short(settings.workspaceId)} / {short(settings.projectId)}</span></div>
    </aside>
    <section className="main">
      <header className="topbar">
        <div><strong>{agent?.name ?? 'Loading agent…'}</strong><div className="code">{workspace?.name ?? short(settings.workspaceId)} · {project?.name ?? short(settings.projectId)} · {provider ? `${provider.embedding.provider}/${provider.embedding.model}` : 'provider not loaded'} {error ? `· ${error}` : ''}</div></div>
        <div className="toolbar"><span className={`chip ${provider?.status === 'ok' ? 'ok' : 'warn'}`}>{provider?.status ?? 'loading'}</span><button className="btn secondary" onClick={() => reload()} disabled={loading}>{loading ? 'Loading…' : 'Reload'}</button></div>
      </header>
      {children}
    </section>
  </div>;
}
