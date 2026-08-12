import { useCallback, useEffect, useState } from 'react'
import { deleteGlossaryEntry, listGlossary } from '../api/client'
import type { GlossaryEntry } from '../types'

export default function GlossaryList({ refreshKey }: { refreshKey: number }) {
  const [items, setItems] = useState<GlossaryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listGlossary()
      setItems(res.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить термбазу')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  const remove = async (id: string) => {
    await deleteGlossaryEntry(id)
    load()
  }

  return (
    <div className="card">
      <div className="memory-list-header">
        <h3>Термбаза ({items.length})</h3>
      </div>
      <div className="memory-table">
        {items.map((item) => (
          <div className="memory-row" key={item.id}>
            <div className="memory-cell">{item.source_term}</div>
            <div className="memory-cell">{item.target_term}</div>
            <div className="memory-meta">
              <span>
                {item.source_lang} → {item.target_lang}
              </span>
              {item.note && <span className="memory-doc-title">{item.note}</span>}
            </div>
            <button className="icon-btn" onClick={() => remove(item.id)} title="Удалить" aria-label="Удалить">
              ✕
            </button>
          </div>
        ))}
        {items.length === 0 && !loading && <div className="empty-state">В термбазе пока ничего нет</div>}
      </div>
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
