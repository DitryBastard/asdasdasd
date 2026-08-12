import { useRef, useState } from 'react'
import { exportMemoryTmx, importMemoryTmx } from '../api/client'
import LanguageSelector from './LanguageSelector'

export default function MemoryImportExport({ onImported }: { onImported: () => void }) {
  const [exporting, setExporting] = useState(false)
  const [importing, setImporting] = useState(false)
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const doExport = async () => {
    setExporting(true)
    setError(null)
    try {
      const blob = await exportMemoryTmx()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'translation-memory.tmx'
      link.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось экспортировать базу')
    } finally {
      setExporting(false)
    }
  }

  const doImport = async (file: File) => {
    setImporting(true)
    setError(null)
    setMessage(null)
    try {
      const res = await importMemoryTmx(file, sourceLang, targetLang, title || file.name)
      setMessage(`Импортировано записей: ${res.added_segments}`)
      onImported()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось импортировать TMX')
    } finally {
      setImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <div className="card">
      <h3>Экспорт / импорт (TMX)</h3>
      <p className="hint">
        TMX — отраслевой формат обмена базами переводов, его понимают большинство CAT-инструментов (Trados, memoQ,
        OmegaT и другие). Экспорт выгружает всю базу целиком; импорт добавляет записи из файла для указанной пары
        языков.
      </p>
      <button className="secondary-btn" onClick={doExport} disabled={exporting}>
        {exporting ? 'Экспортирую…' : '⬇ Экспортировать всю базу в .tmx'}
      </button>
      <div className="lang-bar">
        <LanguageSelector value={sourceLang} onChange={setSourceLang} />
        <span className="lang-arrow">→</span>
        <LanguageSelector value={targetLang} onChange={setTargetLang} />
      </div>
      <input
        className="text-input"
        placeholder="Название источника для импорта (необязательно)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept=".tmx"
        hidden
        onChange={(e) => e.target.files?.[0] && doImport(e.target.files[0])}
      />
      <button className="secondary-btn" onClick={() => fileInputRef.current?.click()} disabled={importing}>
        {importing ? 'Импортирую…' : '⬆ Импортировать .tmx'}
      </button>
      {message && <span className="save-message">{message}</span>}
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
