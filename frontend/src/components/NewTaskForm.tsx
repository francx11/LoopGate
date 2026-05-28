import { useState } from 'react'
import { api } from '../services/api'
import styles from './NewTaskForm.module.css'

export default function NewTaskForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('')
  const [command, setCommand] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (!name.trim() || !command.trim()) {
      setError('Nombre y comando son obligatorios')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.createTask({ name, command, description })
      setName(''); setCommand(''); setDescription('')
      onCreated()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al crear la tarea')
    }
    setLoading(false)
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Nueva tarea</h2>

      <div className={styles.group}>
        <label>Nombre *</label>
        <input
          type="text"
          placeholder="Ej: Deploy producción"
          value={name}
          onChange={e => setName(e.target.value)}
        />
      </div>

      <div className={styles.group}>
        <label>Descripción</label>
        <input
          type="text"
          placeholder="¿Qué hace esta tarea?"
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>

      <div className={styles.group}>
        <label>Comando *</label>
        <textarea
          placeholder="Ej: cd /app && git pull && npm run build"
          value={command}
          onChange={e => setCommand(e.target.value)}
          rows={3}
        />
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <button className={styles.btn} onClick={submit} disabled={loading}>
        {loading ? 'Creando...' : '+ Crear tarea'}
      </button>
    </div>
  )
}
