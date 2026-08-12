import { useRef, useState } from 'react'
import { commitDocumentPairs, downloadTranslatedDocument, translateDocument, translateText } from '../api/client'
import LanguageSelector from '../components/LanguageSelector'
import SegmentedOutput from '../components/SegmentedOutput'
import TranslationReview from '../components/TranslationReview'
import type { TranslateResponse } from '../types'

export default function TranslatePage() {
  const [sourceLang, setSourceLang] = useState('ru')
  const [targetLang, setTargetLang] = useState('en')
  const [sourceText, setSourceText] = useState('')
  const [result, setResult] = useState<TranslateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [reviewMode, setReviewMode] = useState(false)
  const [saveTitle, setSaveTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const swapLanguages = () => {
    setSourceLang(targetLang)
    setTargetLang(sourceLang)
  }

  const resetReviewState = () => {
    setReviewMode(false)
    setSaveMessage(null)
    setSaveTitle('')
  }

  const runTranslate = async () => {
    if (!sourceText.trim()) return
    setLoading(true)
    setError(null)
    try {
      setResult(await translateText(sourceText, sourceLang, targetLang))
      resetReviewState()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось выполнить перевод')
    } finally {
      setLoading(false)
    }
  }

  const onFileChosen = async (file: File) => {
    setLoading(true)
    setError(null)
    setUploadedFile(file)
    try {
      const res = await translateDocument(file, sourceLang, targetLang)
      setSourceText(res.segments.map((s) => s.source).join('\n\n'))
      setResult(res)
      resetReviewState()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обработать документ')
    } finally {
      setLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const downloadFormatted = async () => {
    if (!uploadedFile) return
    setDownloading(true)
    setError(null)
    try {
      const { blob, filename } = await downloadTranslatedDocument(uploadedFile, sourceLang, targetLang)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось собрать файл с переводом')
    } finally {
      setDownloading(false)
    }
  }

  const editSegment = (index: number, value: string) => {
    if (!result) return
    const segments = result.segments.slice()
    segments[index] = { ...segments[index], translation: value }
    setResult({ ...result, segments })
  }

  const saveToMemory = async () => {
    if (!result) return
    const pairs = result.segments
      .filter((s) => s.source.trim() && s.translation.trim())
      .map((s) => ({ source_text: s.source, target_text: s.translation }))
    if (pairs.length === 0) return
    setSaving(true)
    setSaveMessage(null)
    setError(null)
    try {
      const res = await commitDocumentPairs(pairs, sourceLang, targetLang, saveTitle || 'Перевод из интерфейса')
      setSaveMessage(`Сохранено в базу: ${res.added_segments} записей.`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить перевод в базу')
    } finally {
      setSaving(false)
    }
  }

  const matchCount = result?.segments.filter((s) => s.match).length ?? 0
  const canDownloadFormatted = Boolean(uploadedFile?.name.toLowerCase().endsWith('.docx') && result)

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
            onChange={(e) => {
              setSourceText(e.target.value)
              setUploadedFile(null)
            }}
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
              {reviewMode ? (
                <TranslationReview segments={result.segments} onEdit={editSegment} />
              ) : (
                <SegmentedOutput segments={result.segments} />
              )}
              <div className="panel-footer match-summary">
                <span>
                  {matchCount > 0
                    ? `Совпадений с базой: ${matchCount} из ${result.segments.length} предложений.`
                    : 'Совпадений с базой переводов не найдено — перевод выполнен моделью с нуля.'}
                </span>
                <div className="output-actions">
                  <button className="secondary-btn" onClick={() => setReviewMode((v) => !v)}>
                    {reviewMode ? 'Свернуть правку' : '✎ Просмотр и правка'}
                  </button>
                  {canDownloadFormatted && (
                    <button className="secondary-btn" onClick={downloadFormatted} disabled={downloading}>
                      {downloading ? 'Собираю файл…' : 'Скачать .docx с оригинальным форматированием'}
                    </button>
                  )}
                </div>
              </div>
              {reviewMode && (
                <div className="panel-footer save-to-memory">
                  <input
                    className="text-input"
                    placeholder="Название источника (необязательно)"
                    value={saveTitle}
                    onChange={(e) => setSaveTitle(e.target.value)}
                  />
                  <button className="primary-btn" onClick={saveToMemory} disabled={saving}>
                    {saving ? 'Сохраняю…' : 'Сохранить перевод в базу'}
                  </button>
                  {saveMessage && <span className="save-message">{saveMessage}</span>}
                </div>
              )}
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
