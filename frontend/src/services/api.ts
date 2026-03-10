import { useStore } from '../store'

function getBase() {
  return useStore.getState().config?.apiUrl ?? ''
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${getBase()}/api/v1${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getTasks: () => request<any[]>('GET', '/tasks'),

  createTask: (data: { name: string; command: string; description?: string }) =>
    request<any>('POST', '/tasks', data),

  approveTask: (id: string, action: 'approve' | 'reject', reason = '') =>
    request<any>('POST', `/tasks/${id}/approve`, { action, reason }),

  deleteTask: (id: string) =>
    request<any>('DELETE', `/tasks/${id}`),
}
