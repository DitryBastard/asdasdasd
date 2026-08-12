import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import GlossaryPage from './pages/GlossaryPage'
import MemoryPage from './pages/MemoryPage'
import TranslatePage from './pages/TranslatePage'
import type { HealthResponse } from './types'

type Tab = 'translate' | 'memory' | 'glossary'
type StatusLevel = 'ok' | 'warn' | 'down'

function describeStatus(health: HealthResponse | null): { level: StatusLevel; label: string } {
  if (!health) return { level: 'down', label: 'Проверка соединения…' }
  if (!health.ollama_reachable) {
    return { level: 'down', label: 'Ollama недоступна — запустите её локально' }
  }

  const missing = [
    !health.chat_model_available && health.chat_model,
    !health.embed_model_available && health.embed_model,
  ].filter((model): model is string => Boolean(model))

  if (missing.length > 0) {
    const pullCommands = missing.map((model) => `ollama pull ${model}`).join('  /  ')
    return {
      level: 'warn',
      label: `Ollama подключена, но не скачаны модели: ${missing.join(', ')} — выполните: ${pullCommands}`,
    }
  }

  return {
    level: 'ok',
    label: `Ollama подключена · ${health.chat_model} · ${health.memory_count} записей в базе`,
  }
}

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

  const { level, label } = describeStatus(health)

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
          <button className={tab === 'glossary' ? 'tab active' : 'tab'} onClick={() => setTab('glossary')}>
            Термбаза
          </button>
        </nav>
        <div className={`status status-${level}`}>
          <span className="status-dot" />
          {label}
        </div>
      </header>
      <main className="app-main">
        {tab === 'translate' && <TranslatePage />}
        {tab === 'memory' && <MemoryPage />}
        {tab === 'glossary' && <GlossaryPage />}
      </main>
    </div>
  )
}
