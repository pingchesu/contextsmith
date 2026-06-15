'use client';

import type { FormEvent } from 'react';
import { PageHeader, Card, Metric, StatusChip } from '../../components/ui';
import { usePlatform } from '../../lib/platform-context';

export default function LoginPage() {
  const { settings, setSettings, workspace, project, provider, reload } = usePlatform();
  const signedInAs = settings.bearer.trim() ? 'Bearer token principal' : settings.email.trim() || 'Signed out';

  function applyLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const next = {
      apiBaseUrl: String(formData.get('apiBaseUrl') ?? '').trim(),
      email: String(formData.get('email') ?? '').trim(),
      bearer: String(formData.get('bearer') ?? '').trim(),
      workspaceId: String(formData.get('workspaceId') ?? '').trim(),
      projectId: String(formData.get('projectId') ?? '').trim(),
    };
    setSettings(next);
    void reload();
  }

  function logout() {
    setSettings({ ...settings, bearer: '', email: '' });
  }

  return <main className="page">
    <PageHeader eyebrow="Session" title="Login / logout" description="This console uses ContextSmith dev-auth headers or a scoped bearer token. Login controls the principal used by User Management, resource review, repo-agent generation, and admin views." />
    <div className="grid four">
      <Metric label="Current principal" value={signedInAs} />
      <Metric label="Workspace" value={workspace?.name ?? '—'} />
      <Metric label="Project" value={project?.name ?? '—'} />
      <div className="metric"><div className="metric-label">Provider</div><div className="metric-value"><StatusChip value={provider?.status ?? 'signed-out'} /></div></div>
    </div>
    <div className="grid two">
      <Card>
        <h2>Login</h2>
        <p className="muted">Use email for local/dev auth, or paste an API token for bearer auth. Tokens stay in session storage; email/workspace/project persist as console preferences.</p>
        <form className="grid" onSubmit={applyLogin}>
          <label><span className="label">API base URL</span><input name="apiBaseUrl" className="input" defaultValue={settings.apiBaseUrl} /></label>
          <label><span className="label">Dev auth email</span><input name="email" className="input" placeholder="user@example.com" defaultValue={settings.email} /></label>
          <label><span className="label">Bearer token (optional)</span><input name="bearer" className="input" type="password" placeholder="cs_..." defaultValue={settings.bearer} /></label>
          <label><span className="label">Workspace ID</span><input name="workspaceId" className="input" defaultValue={settings.workspaceId} /></label>
          <label><span className="label">Project ID</span><input name="projectId" className="input" defaultValue={settings.projectId} /></label>
          <div className="toolbar"><button className="btn" type="submit">Login / switch session</button><button className="btn danger" type="button" onClick={logout}>Logout</button></div>
        </form>
      </Card>
      <Card>
        <h2>Why this matters</h2>
        <div className="grid">
          <div className="notice">User Management now reflects the active principal. If you logout, the console intentionally stops loading workspace/project/member/token data.</div>
          <ul className="muted">
            <li>Email login sends the X-User-Email dev-auth header.</li>
            <li>Bearer login sends the Authorization bearer token header.</li>
            <li>Read-only tokens should not see workspace member emails.</li>
            <li>Admin operations require admin-capable user/token scope.</li>
          </ul>
        </div>
      </Card>
    </div>
  </main>;
}
