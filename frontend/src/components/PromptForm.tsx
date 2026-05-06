import { useState } from 'react'
import { api } from '../services/api'
import styles from './PromptForm.module.css'

export default function PromptForm({ onCreated }: { onCreated: () => void }) {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    const text = prompt.trim()
    if (!text) { setError('Escribe un prompt'); return }
    setLoading(true)
    setError('')
    try {
      const escaped = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
      await api.createTask({
        name: text.slice(0, 60),
        command: `claude -p "${escaped}"`,
        description: 'Prompt Claude Code',
      })
      setPrompt('')
      onCreated()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al enviar')
    }
    setLoading(false)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.icon}>🤖</span>
        <div>
          <div className={styles.title}>Prompt a Claude Code</div>
          <div className={styles.sub}>El agente ejecutará la instrucción en tu PC local</div>
        </div>
      </div>

      <textarea
        className={styles.textarea}
        placeholder="Ej: Crea un script Python que lea todos los .log del escritorio y genere un resumen..."
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={onKeyDown}
        rows={6}
        autoFocus
      />

      {error && <p className={styles.error}>{error}</p>}

      <button
        className={styles.btn}
        onClick={submit}
        disabled={loading || !prompt.trim()}
      >
        {loading ? 'Enviando...' : '→ Enviar a Claude Code'}
      </button>

      <p className={styles.hint}>
        Requiere aprobación antes de ejecutar · Ctrl+Enter para enviar
      </p>
    </div>
  )
}
