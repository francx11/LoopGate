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
  claude_session_id: string | null
  claude_result: string | null
  claude_cost_usd: number | null
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

  // Sessions: project_path → session_id
  sessions: Record<string, string>

  // Actions
  setConfig: (config: Config) => void
  setConnected: (v: boolean) => void
  setWs: (ws: WebSocket | null) => void
  setTasks: (tasks: Task[]) => void
  upsertTask: (task: Task) => void
  appendLog: (taskId: string, line: LogLine) => void
  deleteTask: (taskId: string) => void
  setSessions: (sessions: Record<string, string>) => void
  upsertSession: (projectPath: string, sessionId: string) => void
  deleteSession: (projectPath: string) => void
  disconnect: () => void
}

export const useStore = create<AppState>((set, get) => ({
  config: null,
  connected: false,
  ws: null,
  tasks: {},
  sessions: {},

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

  setSessions: (sessions) => set({ sessions }),

  upsertSession: (projectPath, sessionId) =>
    set((s) => ({ sessions: { ...s.sessions, [projectPath]: sessionId } })),

  deleteSession: (projectPath) =>
    set((s) => {
      const next = { ...s.sessions }
      delete next[projectPath]
      return { sessions: next }
    }),

  disconnect: () => {
    get().ws?.close()
    set({ config: null, connected: false, ws: null, tasks: {}, sessions: {} })
  },
}))
