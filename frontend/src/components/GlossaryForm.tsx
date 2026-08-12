import { useState } from 'react'
import { addGlossaryEntry } from '../api/client'
import LanguageSelector from './LanguageSelector'

export default function GlossaryForm({ onAdded }: { onAdded: () => void }) {
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [sourceTerm, setSourceTerm] = useState('')
  const [targetTerm, setTargetTerm] = useState('')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!sourceTerm.trim() || !targetTerm.trim()) return
    setSaving(true)
    setError(null)
    try {
      await addGlossaryEntry({
        source_term: sourceTerm,
        target_term: targetTerm,
        source_lang: sourceLang,
        target_lang: targetLang,
        note,
      })
      setSourceTerm('')
      setTargetTerm('')
      setNote('')
      onAdded()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить термин')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <h3>Добавить обязательный термин</h3>
      <p className="hint">
        В отличие от базы переводов, термин применяется точным совпадением текста, а не по смыслу — модель обязана
        использовать именно этот перевод каждый раз, когда термин встречается в исходном тексте.
      </p>
      <div className="lang-bar">
        <LanguageSelector value={sourceLang} onChange={setSourceLang} />
        <span className="lang-arrow">→</span>
        <LanguageSelector value={targetLang} onChange={setTargetLang} />
      </div>
      <input
        className="text-input"
        placeholder="Термин в оригинале"
        value={sourceTerm}
        onChange={(e) => setSourceTerm(e.target.value)}
      />
      <input
        className="text-input"
        placeholder="Обязательный перевод"
        value={targetTerm}
        onChange={(e) => setTargetTerm(e.target.value)}
      />
      <input
        className="text-input"
        placeholder="Примечание (необязательно)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <button className="primary-btn" onClick={submit} disabled={saving || !sourceTerm.trim() || !targetTerm.trim()}>
        {saving ? 'Сохраняю…' : 'Добавить термин'}
      </button>
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
