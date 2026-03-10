import { useState, useEffect } from 'react'
import { useStore } from './store'
import { useWebSocket } from './hooks/useWebSocket'
import SetupScreen from './pages/SetupScreen'
import Dashboard from './pages/Dashboard'

export default function App() {
  const { config } = useStore()
  return config ? <Main /> : <SetupScreen />
}

function Main() {
  useWebSocket()
  return <Dashboard />
}
