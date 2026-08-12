import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import MemoryPage from './pages/MemoryPage'
import TranslatePage from './pages/TranslatePage'
import type { HealthResponse } from './types'

type Tab = 'translate' | 'memory'

export default function App() {
  const [tab, setTab] = useState<Tab>('translate')
  const [health, setHealth] = useState<HealthResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    const check = () => {
      getHealth()
        .then((h) => !cancelled && setHealth(h))
        .catch(() => !cancelled && setHealth(null))
    }
    check()
    const interval = setInterval(check, 15000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  const statusLabel = health
    ? health.ollama_reachable
      ? `Ollama подключена · ${health.chat_model} · ${health.memory_count} записей в базе`
      : 'Ollama недоступна — запустите её локально'
    : 'Проверка соединения…'

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-title">AI Переводчик</div>
        <nav className="tabs">
          <button className={tab === 'translate' ? 'tab active' : 'tab'} onClick={() => setTab('translate')}>
            Перевод
          </button>
          <button className={tab === 'memory' ? 'tab active' : 'tab'} onClick={() => setTab('memory')}>
            База переводов
          </button>
        </nav>
        <div className={`status ${health?.ollama_reachable ? 'status-ok' : 'status-down'}`}>
          <span className="status-dot" />
          {statusLabel}
        </div>
      </header>
      <main className="app-main">{tab === 'translate' ? <TranslatePage /> : <MemoryPage />}</main>
    </div>
  )
}
