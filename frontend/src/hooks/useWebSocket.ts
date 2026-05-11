import { useEffect, useRef } from 'react'
import { useStore } from '../store'

const HEARTBEAT_INTERVAL = 30_000
const HEARTBEAT_TIMEOUT = 5_000
const RECONNECT_BASE = 3_000
const RECONNECT_MAX = 30_000
const AUTH_FAIL_THRESHOLD = 3  // consecutive fast-fail closes before giving up

export function useWebSocket() {
  const { config, setConnected, setWs, setTasks, upsertTask, appendLog, deleteTask, disconnect } = useStore()

  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const heartbeatTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pongTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelay = useRef(RECONNECT_BASE)

  useEffect(() => {
    let currentSocket: WebSocket | null = null
    let destroyed = false
    let fastFailCount = 0
    let connectTime = 0

    function scheduleHeartbeat() {
      if (heartbeatTimer.current) clearTimeout(heartbeatTimer.current)
      heartbeatTimer.current = setTimeout(() => {
        if (!currentSocket || currentSocket.readyState !== WebSocket.OPEN) return
        try {
          currentSocket.send(JSON.stringify({ type: 'ping' }))
        } catch {
          currentSocket.close()
          return
        }
        // Close the socket if no pong arrives — triggers onclose → reconnect
        pongTimer.current = setTimeout(() => {
          currentSocket?.close()
        }, HEARTBEAT_TIMEOUT)
      }, HEARTBEAT_INTERVAL)
    }

    function scheduleReconnect() {
      if (reconnectTimer.current || destroyed) return
      reconnectTimer.current = setTimeout(() => {
        reconnectTimer.current = null
        if (!destroyed) connect()
      }, reconnectDelay.current)
      reconnectDelay.current = Math.min(reconnectDelay.current * 2, RECONNECT_MAX)
    }

    function connect() {
      if (!config || destroyed) return

      const socket = new WebSocket(config.wsUrl)
      currentSocket = socket
      connectTime = Date.now()

      socket.onopen = () => {
        if (destroyed) { socket.close(); return }
        // Auth via first message — keeps the token out of proxy access logs
        // and lets the server reject without a pre-accept HTTP 403.
        try {
          socket.send(JSON.stringify({ type: 'auth', token: config.token ?? '' }))
        } catch {
          socket.close()
          return
        }
        fastFailCount = 0
        setConnected(true)
        setWs(socket)
        reconnectDelay.current = RECONNECT_BASE
        scheduleHeartbeat()
      }

      socket.onmessage = (e) => {
        // Any incoming message resets the zombie-detection timer
        if (pongTimer.current) { clearTimeout(pongTimer.current); pongTimer.current = null }
        scheduleHeartbeat()
        const msg = JSON.parse(e.data)
        if (msg.type === 'pong') return
        if (msg.type === 'auth_error') {
          // Token rejected post-handshake. Drop config so SetupScreen reappears
          // and the user can re-enter the right token.
          disconnect()
          return
        }
        if (msg.type === 'init') setTasks(msg.tasks)
        else if (msg.type === 'task_created') upsertTask(msg.task)
        else if (msg.type === 'task_updated') upsertTask(msg.task)
        else if (msg.type === 'task_log') appendLog(msg.task_id, msg.line)
        else if (msg.type === 'task_deleted') deleteTask(msg.task_id)
      }

      socket.onclose = () => {
        if (heartbeatTimer.current) { clearTimeout(heartbeatTimer.current); heartbeatTimer.current = null }
        if (pongTimer.current) { clearTimeout(pongTimer.current); pongTimer.current = null }
        setConnected(false)
        // A close within 1 s of connecting (before onopen) means the server
        // rejected the handshake — likely a 403 auth failure.
        const wasInstant = Date.now() - connectTime < 1000
        if (wasInstant) {
          fastFailCount++
          if (fastFailCount >= AUTH_FAIL_THRESHOLD) {
            // Persistent rejection — clear config so SetupScreen is shown.
            disconnect()
            return
          }
        }
        scheduleReconnect()
      }

      socket.onerror = () => setConnected(false)
    }

    connect()

    return () => {
      destroyed = true
      if (reconnectTimer.current) { clearTimeout(reconnectTimer.current); reconnectTimer.current = null }
      if (heartbeatTimer.current) { clearTimeout(heartbeatTimer.current); heartbeatTimer.current = null }
      if (pongTimer.current) { clearTimeout(pongTimer.current); pongTimer.current = null }
      currentSocket?.close()
    }
  }, [config, setConnected, setWs, setTasks, upsertTask, appendLog, deleteTask, disconnect])
}
