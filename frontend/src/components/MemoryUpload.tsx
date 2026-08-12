import { useState } from 'react'
import { commitDocumentPairs, previewDocumentPair } from '../api/client'
import type { DocumentPairPreview } from '../types'
import LanguageSelector from './LanguageSelector'

export default function MemoryUpload({ onCommitted }: { onCommitted: () => void }) {
  const [sourceFile, setSourceFile] = useState<File | null>(null)
  const [targetFile, setTargetFile] = useState<File | null>(null)
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [title, setTitle] = useState('')
  const [preview, setPreview] = useState<DocumentPairPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runPreview = async () => {
    if (!sourceFile || !targetFile) return
    setLoading(true)
    setError(null)
    try {
      const res = await previewDocumentPair(sourceFile, targetFile)
      setPreview(res)
      if (!title) setTitle(sourceFile.name)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось разобрать документы')
    } finally {
      setLoading(false)
    }
  }

  const updatePair = (index: number, field: 'source_text' | 'target_text', value: string) => {
    if (!preview) return
    const pairs = preview.pairs.slice()
    pairs[index] = { ...pairs[index], [field]: value }
    setPreview({ ...preview, pairs })
  }

  const removePair = (index: number) => {
    if (!preview) return
    setPreview({ ...preview, pairs: preview.pairs.filter((_, i) => i !== index) })
  }

  const commit = async () => {
    if (!preview || preview.pairs.length === 0) return
    setLoading(true)
    setError(null)
    try {
      await commitDocumentPairs(preview.pairs, sourceLang, targetLang, title || 'Документ')
      setPreview(null)
      setSourceFile(null)
      setTargetFile(null)
      setTitle('')
      onCommitted()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить документ в базу')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3>Загрузить пару документов (оригинал + перевод)</h3>
      <div className="lang-bar">
        <LanguageSelector value={sourceLang} onChange={setSourceLang} />
        <span className="lang-arrow">→</span>
        <LanguageSelector value={targetLang} onChange={setTargetLang} />
      </div>
      <div className="upload-row">
        <label className="file-label">
          Оригинал (.docx / .pdf)
          <input type="file" accept=".docx,.pdf,.txt" onChange={(e) => setSourceFile(e.target.files?.[0] ?? null)} />
          {sourceFile && <span className="file-name">{sourceFile.name}</span>}
        </label>
        <label className="file-label">
          Перевод (.docx / .pdf)
          <input type="file" accept=".docx,.pdf,.txt" onChange={(e) => setTargetFile(e.target.files?.[0] ?? null)} />
          {targetFile && <span className="file-name">{targetFile.name}</span>}
        </label>
      </div>
      <input className="text-input" placeholder="Название документа" value={title} onChange={(e) => setTitle(e.target.value)} />
      <button className="secondary-btn" onClick={runPreview} disabled={!sourceFile || !targetFile || loading}>
        {loading && !preview ? 'Обрабатываю…' : 'Сопоставить абзацы'}
      </button>

      {preview && (
        <div className="alignment-preview">
          <p className="hint">
            Абзацы сопоставлены по порядку ({preview.source_paragraph_count} в оригинале, {preview.target_paragraph_count} в
            переводе). Проверьте пары и удалите неверные перед сохранением.
          </p>
          <div className="pair-table">
            <div className="pair-row pair-row-header">
              <span>Оригинал</span>
              <span>Перевод</span>
              <span />
            </div>
            {preview.pairs.map((pair, idx) => (
              <div className="pair-row" key={idx}>
                <textarea
                  className="pair-cell"
                  value={pair.source_text}
                  onChange={(e) => updatePair(idx, 'source_text', e.target.value)}
                />
                <textarea
                  className="pair-cell"
                  value={pair.target_text}
                  onChange={(e) => updatePair(idx, 'target_text', e.target.value)}
                />
                <button className="icon-btn" onClick={() => removePair(idx)} title="Удалить пару" aria-label="Удалить пару">
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button className="primary-btn" onClick={commit} disabled={loading || preview.pairs.length === 0}>
            {loading ? 'Сохраняю…' : `Добавить ${preview.pairs.length} пар в базу`}
          </button>
        </div>
      )}
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
