export type PlatformSettings = {
  apiBaseUrl: string;
  email: string;
  bearer: string;
  workspaceId: string;
  projectId: string;
};

export const DEFAULT_SETTINGS: PlatformSettings = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:18000',
  email: process.env.NEXT_PUBLIC_CONTEXTSMITH_EMAIL ?? 'angiknowledge-repo-agent@example.com',
  bearer: '',
  workspaceId: process.env.NEXT_PUBLIC_CONTEXTSMITH_WORKSPACE_ID ?? '055e3999-6720-48dc-aa19-7f8cb44907d0',
  projectId: process.env.NEXT_PUBLIC_CONTEXTSMITH_PROJECT_ID ?? '8cea8aed-3006-4236-b626-3b77e5724aaf',
};

const STORAGE_KEY = 'contextsmith.platform.settings.v1';
const SESSION_SECRET_KEY = 'contextsmith.platform.bearer.v1';

export function loadSettings(): PlatformSettings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const sessionBearer = window.sessionStorage.getItem(SESSION_SECRET_KEY) ?? '';
    const parsed = raw ? JSON.parse(raw) : {};
    return { ...DEFAULT_SETTINGS, ...parsed, bearer: sessionBearer };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: PlatformSettings): void {
  if (typeof window === 'undefined') return;
  const { bearer, ...persisted } = settings;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  window.sessionStorage.setItem(SESSION_SECRET_KEY, bearer);
}
