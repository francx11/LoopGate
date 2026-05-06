import { create } from 'zustand'

export type TaskStatus =
  | 'pending_approval'
  | 'queued'
  | 'running'
  | 'done'
  | 'error'
  | 'rejected'

export interface LogLine {
  time: string
  text: string
}

export interface Task {
  id: string
  name: string
  command: string
  description: string
  status: TaskStatus
  created_at: string
  started_at: string | null
  finished_at: string | null
  exit_code: number | null
  reject_reason: string | null
  log: LogLine[]
}

interface Config {
  apiUrl: string
  wsUrl: string
  token: string
}

interface AppState {
  // Connection
  config: Config | null
  connected: boolean
  ws: WebSocket | null

  // Tasks
  tasks: Record<string, Task>

  // Actions
  setConfig: (config: Config) => void
  setConnected: (v: boolean) => void
  setWs: (ws: WebSocket | null) => void
  setTasks: (tasks: Task[]) => void
  upsertTask: (task: Task) => void
  appendLog: (taskId: string, line: LogLine) => void
  deleteTask: (taskId: string) => void
  disconnect: () => void
}

export const useStore = create<AppState>((set, get) => ({
  config: null,
  connected: false,
  ws: null,
  tasks: {},

  setConfig: (config) => set({ config }),
  setConnected: (connected) => set({ connected }),
  setWs: (ws) => set({ ws }),

  setTasks: (tasks) => {
    const map: Record<string, Task> = {}
    tasks.forEach((t) => (map[t.id] = t))
    set({ tasks: map })
  },

  upsertTask: (task) =>
    set((s) => ({ tasks: { ...s.tasks, [task.id]: task } })),

  appendLog: (taskId, line) =>
    set((s) => {
      const task = s.tasks[taskId]
      if (!task) return s
      return {
        tasks: {
          ...s.tasks,
          [taskId]: { ...task, log: [...task.log, line] },
        },
      }
    }),

  deleteTask: (taskId) =>
    set((s) => {
      const next = { ...s.tasks }
      delete next[taskId]
      return { tasks: next }
    }),

  disconnect: () => {
    get().ws?.close()
    set({ config: null, connected: false, ws: null, tasks: {} })
  },
}))
