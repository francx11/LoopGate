import { useStore } from '../store'

function getBase() {
  return useStore.getState().config?.apiUrl ?? ''
}

function getToken() {
  return useStore.getState().config?.token ?? ''
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
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getProjects: () => request<{ name: string; path: string }[]>('GET', '/projects'),

  getTasks: () => request<any[]>('GET', '/tasks'),

  createTask: (data: { name: string; command: string; description?: string }) =>
    request<any>('POST', '/tasks', data),

  approveTask: (id: string, action: 'approve' | 'reject', reason = '') =>
    request<any>('POST', `/tasks/${id}/approve`, { action, reason }),

  deleteTask: (id: string) =>
    request<any>('DELETE', `/tasks/${id}`),
}
