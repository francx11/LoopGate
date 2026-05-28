import { useStore, Task } from '../store'

function getBase() {
  return useStore.getState().config?.apiUrl ?? ''
}

function getToken() {
  return useStore.getState().config?.token ?? ''
}

function handleAuthFailure() {
  // Stale or wrong token. Drop it so SetupScreen re-prompts on the next render.
  localStorage.removeItem('lg-token')
  useStore.getState().disconnect()
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = getToken()
  const res = await fetch(`${getBase()}/api/v1${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      handleAuthFailure()
    }
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getProjects: () => request<{ name: string; path: string }[]>('GET', '/projects'),

  getTasks: () => request<Task[]>('GET', '/tasks'),

  createTask: (data: { name: string; command: string; description?: string }) =>
    request<Task>('POST', '/tasks', data),

  createClaudePrompt: (data: { prompt: string; project_path: string; new_session?: boolean }) =>
    request<Task>('POST', '/tasks/claude-prompt', data),

  approveTask: (id: string, action: 'approve' | 'reject', reason = '') =>
    request<{ ok: boolean; message: string }>('POST', `/tasks/${id}/approve`, { action, reason }),

  deleteTask: (id: string) =>
    request<{ ok: boolean }>('DELETE', `/tasks/${id}`),

  getSessions: () =>
    request<Record<string, string>>('GET', '/sessions'),

  clearSession: (projectPath: string) =>
    request<{ ok: boolean; deleted: boolean }>('DELETE', `/sessions?project_path=${encodeURIComponent(projectPath)}`),
}
