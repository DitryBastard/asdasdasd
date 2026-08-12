import { useRef, useState } from 'react'
import { translateDocument, translateText } from '../api/client'
import LanguageSelector from '../components/LanguageSelector'
import SegmentedOutput from '../components/SegmentedOutput'
import type { TranslateResponse } from '../types'

export default function TranslatePage() {
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [sourceText, setSourceText] = useState('')
  const [result, setResult] = useState<TranslateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const swapLanguages = () => {
    setSourceLang(targetLang)
    setTargetLang(sourceLang)
  }

  const runTranslate = async () => {
    if (!sourceText.trim()) return
    setLoading(true)
    setError(null)
    try {
      setResult(await translateText(sourceText, sourceLang, targetLang))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось выполнить перевод')
    } finally {
      setLoading(false)
    }
  }

  const onFileChosen = async (file: File) => {
    setLoading(true)
    setError(null)
    try {
      const res = await translateDocument(file, sourceLang, targetLang)
      setSourceText(res.segments.map((s) => s.source).join('\n\n'))
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обработать документ')
    } finally {
      setLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const matchCount = result?.segments.filter((s) => s.match).length ?? 0

  return (
    <div className="translate-page">
      <div className="lang-bar">
        <LanguageSelector value={sourceLang} onChange={setSourceLang} />
        <button className="swap-btn" onClick={swapLanguages} title="Поменять языки местами" aria-label="Поменять языки местами">
          ⇄
        </button>
        <LanguageSelector value={targetLang} onChange={setTargetLang} />
        <div className="lang-bar-spacer" />
        <input
          ref={fileInputRef}
          type="file"
          accept=".docx,.pdf,.txt"
          hidden
          onChange={(e) => e.target.files?.[0] && onFileChosen(e.target.files[0])}
        />
        <button className="secondary-btn" onClick={() => fileInputRef.current?.click()}>
          Загрузить файл (.docx, .pdf)
        </button>
      </div>

      <div className="translate-grid">
        <div className="panel">
          <textarea
            className="source-textarea"
            placeholder="Вставьте текст для перевода…"
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
          />
          <div className="panel-footer">
            <button className="primary-btn" onClick={runTranslate} disabled={loading || !sourceText.trim()}>
              {loading ? 'Перевожу…' : 'Перевести'}
            </button>
          </div>
        </div>

        <div className="panel">
          {result ? (
            <>
              <SegmentedOutput segments={result.segments} />
              <div className="panel-footer match-summary">
                {matchCount > 0
                  ? `Совпадений с базой: ${matchCount} из ${result.segments.length} предложений. Нажмите на выделенный текст, чтобы увидеть источник.`
                  : 'Совпадений с базой переводов не найдено — перевод выполнен моделью с нуля.'}
              </div>
            </>
          ) : (
            <div className="output-placeholder">Здесь появится перевод</div>
          )}
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
