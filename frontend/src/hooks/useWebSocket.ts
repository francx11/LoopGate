import { useEffect, useCallback } from 'react'
import { useStore } from '../store'

export function useWebSocket() {
  const { config, setConnected, setWs, setTasks, upsertTask, appendLog, deleteTask } = useStore()

  const connect = useCallback(() => {
    if (!config) return
    const wsUrl = config.token
      ? `${config.wsUrl}?token=${encodeURIComponent(config.token)}`
      : config.wsUrl
    const socket = new WebSocket(wsUrl)

    socket.onopen = () => setConnected(true)

    socket.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'init') setTasks(msg.tasks)
      else if (msg.type === 'task_created') upsertTask(msg.task)
      else if (msg.type === 'task_updated') upsertTask(msg.task)
      else if (msg.type === 'task_log') appendLog(msg.task_id, msg.line)
      else if (msg.type === 'task_deleted') deleteTask(msg.task_id)
    }

    socket.onclose = () => {
      setConnected(false)
      setTimeout(connect, 3000) // auto-reconnect
    }

    socket.onerror = () => setConnected(false)

    setWs(socket)
    return socket
  }, [config])

  useEffect(() => {
    const socket = connect()
    return () => socket?.close()
  }, [connect])
}
