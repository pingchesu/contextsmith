'use client';

import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiFetch } from './api';
import { loadSettings, saveSettings, type PlatformSettings } from './settings';
import type { AgentProfile, ApiToken, AuditEvent, GraphRead, IndexRun, Project, ProviderHealth, Resource, ReviewItem, Snapshot, UsageItem, Workspace, WorkspaceMember } from './types';

type PlatformState = {
  settings: PlatformSettings;
  setSettings: (settings: PlatformSettings) => void;
  workspaces: Workspace[];
  workspace: Workspace | null;
  projects: Project[];
  project: Project | null;
  provider: ProviderHealth | null;
  agents: AgentProfile[];
  agent: AgentProfile | null;
  resources: Resource[];
  reviewItems: ReviewItem[];
  usageItems: UsageItem[];
  tokens: ApiToken[];
  members: WorkspaceMember[];
  auditEvents: AuditEvent[];
  selectedResourceId: string;
  selectedResource: Resource | null;
  snapshots: Snapshot[];
  indexRuns: IndexRun[];
  graph: GraphRead | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  selectResource: (resourceId: string) => Promise<void>;
  client: <T>(path: string, init?: RequestInit) => Promise<T>;
};

const PlatformContext = createContext<PlatformState | null>(null);

export function PlatformProvider({ children }: { children: ReactNode }) {
  const [settings, setSettingsState] = useState<PlatformSettings>(loadSettings);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [provider, setProvider] = useState<ProviderHealth | null>(null);
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [agent, setAgent] = useState<AgentProfile | null>(null);
  const [resources, setResources] = useState<Resource[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [usageItems, setUsageItems] = useState<UsageItem[]>([]);
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [selectedResourceId, setSelectedResourceId] = useState('');
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [indexRuns, setIndexRuns] = useState<IndexRun[]>([]);
  const [graph, setGraph] = useState<GraphRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const client = useCallback(<T,>(path: string, init?: RequestInit) => apiFetch<T>(settings, path, init), [settings]);

  const setSettings = useCallback((next: PlatformSettings) => {
    setSettingsState(next);
    saveSettings(next);
  }, []);

  const loadResourceDetails = useCallback(async (resourceId: string) => {
    if (!resourceId) return;
    const { workspaceId, projectId } = settings;
    const [nextSnapshots, nextRuns, nextGraph] = await Promise.all([
      client<Snapshot[]>(`/workspaces/${workspaceId}/projects/${projectId}/resources/${resourceId}/snapshots`),
      client<IndexRun[]>(`/workspaces/${workspaceId}/projects/${projectId}/resources/${resourceId}/index-runs`),
      client<GraphRead>(`/workspaces/${workspaceId}/projects/${projectId}/resources/${resourceId}/graph`).catch(() => null),
    ]);
    setSnapshots(nextSnapshots);
    setIndexRuns(nextRuns);
    setGraph(nextGraph);
  }, [client, settings]);

  const reload = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const { workspaceId, projectId } = settings;
      const [workspaceList, currentWorkspace, projectList, currentProject, providerHealth, nextAgents, nextAgent, nextResources, review, usage, tokenList, memberList, events] = await Promise.all([
        client<Workspace[]>('/workspaces').catch(() => []),
        client<Workspace>(`/workspaces/${workspaceId}`).catch(() => null),
        client<Project[]>(`/workspaces/${workspaceId}/projects`).catch(() => []),
        client<Project>(`/workspaces/${workspaceId}/projects/${projectId}`).catch(() => null),
        client<ProviderHealth>('/provider-health').catch((err) => ({ status: 'degraded', embedding: { namespace: 'unavailable', dev_quality: true, status: 'error', provider: 'unknown', model: String(err) } })),
        client<AgentProfile[]>(`/workspaces/${workspaceId}/agents`),
        client<AgentProfile>(`/workspaces/${workspaceId}/projects/${projectId}/agent-profile`),
        client<Resource[]>(`/workspaces/${workspaceId}/projects/${projectId}/resources`),
        client<{ resources: ReviewItem[] }>(`/workspaces/${workspaceId}/projects/${projectId}/resource-review`),
        client<{ resources: UsageItem[] }>(`/workspaces/${workspaceId}/projects/${projectId}/resource-usage`),
        client<ApiToken[]>(`/workspaces/${workspaceId}/api-tokens`).catch(() => []),
        client<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`).catch(() => []),
        client<AuditEvent[]>(`/workspaces/${workspaceId}/audit-events`).catch(() => []),
      ]);
      setWorkspaces(workspaceList); setWorkspace(currentWorkspace); setProjects(projectList); setProject(currentProject);
      setProvider(providerHealth); setAgents(nextAgents); setAgent(nextAgent); setResources(nextResources); setReviewItems(review.resources); setUsageItems(usage.resources); setTokens(tokenList); setMembers(memberList); setAuditEvents(events);
      const current = nextResources.find((resource) => resource.id === selectedResourceId && resource.status === 'active');
      const preferred = current ?? nextResources.find((resource) => resource.name.includes('AngiBrain') && resource.status === 'active') ?? nextResources[0];
      if (preferred) { setSelectedResourceId(preferred.id); await loadResourceDetails(preferred.id); }
    } catch (err) { setError(String(err)); }
    finally { setLoading(false); }
  }, [client, loadResourceDetails, selectedResourceId, settings]);

  const selectResource = useCallback(async (resourceId: string) => {
    setSelectedResourceId(resourceId); setLoading(true); setError(null);
    try { await loadResourceDetails(resourceId); }
    catch (err) { setError(String(err)); }
    finally { setLoading(false); }
  }, [loadResourceDetails]);

  useEffect(() => { void reload(); }, [reload]);

  const selectedResource = resources.find((resource) => resource.id === selectedResourceId) ?? null;
  const value = useMemo(() => ({ settings, setSettings, workspaces, workspace, projects, project, provider, agents, agent, resources, reviewItems, usageItems, tokens, members, auditEvents, selectedResourceId, selectedResource, snapshots, indexRuns, graph, loading, error, reload, selectResource, client }), [settings, setSettings, workspaces, workspace, projects, project, provider, agents, agent, resources, reviewItems, usageItems, tokens, members, auditEvents, selectedResourceId, selectedResource, snapshots, indexRuns, graph, loading, error, reload, selectResource, client]);
  return <PlatformContext.Provider value={value}>{children}</PlatformContext.Provider>;
}

export function usePlatform() {
  const value = useContext(PlatformContext);
  if (!value) throw new Error('usePlatform must be used inside PlatformProvider');
  return value;
}
