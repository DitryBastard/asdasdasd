import { useState } from 'react'
import { addManualEntry } from '../api/client'
import LanguageSelector from './LanguageSelector'

export default function ManualEntryForm({ onAdded }: { onAdded: () => void }) {
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [sourceText, setSourceText] = useState('')
  const [targetText, setTargetText] = useState('')
  const [title, setTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!sourceText.trim() || !targetText.trim()) return
    setSaving(true)
    setError(null)
    try {
      await addManualEntry({
        source_text: sourceText,
        target_text: targetText,
        source_lang: sourceLang,
        target_lang: targetLang,
        document_title: title || 'Ручное добавление',
      })
      setSourceText('')
      setTargetText('')
      onAdded()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить запись')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <h3>Добавить пару вручную</h3>
      <div className="lang-bar">
        <LanguageSelector value={sourceLang} onChange={setSourceLang} />
        <span className="lang-arrow">→</span>
        <LanguageSelector value={targetLang} onChange={setTargetLang} />
      </div>
      <textarea
        className="small-textarea"
        placeholder="Исходный текст"
        value={sourceText}
        onChange={(e) => setSourceText(e.target.value)}
      />
      <textarea
        className="small-textarea"
        placeholder="Перевод"
        value={targetText}
        onChange={(e) => setTargetText(e.target.value)}
      />
      <input
        className="text-input"
        placeholder="Название источника (необязательно)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <button className="primary-btn" onClick={submit} disabled={saving || !sourceText.trim() || !targetText.trim()}>
        {saving ? 'Сохраняю…' : 'Добавить в базу'}
      </button>
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
