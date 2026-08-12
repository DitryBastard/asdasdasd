import { useCallback, useEffect, useState } from 'react'
import { deleteMemoryEntry, listMemory } from '../api/client'
import type { MemoryItem } from '../types'

export default function MemoryList({ refreshKey }: { refreshKey: number }) {
  const [items, setItems] = useState<MemoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listMemory({ query: query || undefined, limit: 50 })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить базу')
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  const remove = async (id: string) => {
    await deleteMemoryEntry(id)
    load()
  }

  return (
    <div className="card">
      <div className="memory-list-header">
        <h3>База переводов ({total})</h3>
        <input
          className="text-input"
          placeholder="Поиск по смыслу…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
        />
        <button className="secondary-btn" onClick={load} disabled={loading}>
          {loading ? 'Ищу…' : 'Искать'}
        </button>
      </div>
      <div className="memory-table">
        {items.map((item) => (
          <div className="memory-row" key={item.id}>
            <div className="memory-cell">{item.source_text}</div>
            <div className="memory-cell">{item.target_text}</div>
            <div className="memory-meta">
              <span>
                {item.source_lang} → {item.target_lang}
              </span>
              <span className="memory-doc-title">{item.document_title}</span>
            </div>
            <button className="icon-btn" onClick={() => remove(item.id)} title="Удалить" aria-label="Удалить">
              ✕
            </button>
          </div>
        ))}
        {items.length === 0 && !loading && <div className="empty-state">В базе пока ничего нет</div>}
      </div>
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
