import type {
  DocumentPair,
  DocumentPairPreview,
  GlossaryEntry,
  GlossaryListResponse,
  HealthResponse,
  MemoryListResponse,
  TranslateResponse,
} from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export function getHealth(): Promise<HealthResponse> {
  return request('/api/health')
}

export function translateText(text: string, sourceLang: string, targetLang: string): Promise<TranslateResponse> {
  return request('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
  })
}

export function translateDocument(file: File, sourceLang: string, targetLang: string): Promise<TranslateResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('source_lang', sourceLang)
  form.append('target_lang', targetLang)
  return request('/api/translate/document', { method: 'POST', body: form })
}

function parseFilename(contentDisposition: string | null, fallback: string): string {
  if (!contentDisposition) return fallback
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) return decodeURIComponent(utf8Match[1])
  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
  return plainMatch ? plainMatch[1] : fallback
}

export async function downloadTranslatedDocument(
  file: File,
  sourceLang: string,
  targetLang: string,
): Promise<{ blob: Blob; filename: string }> {
  const form = new FormData()
  form.append('file', file)
  form.append('source_lang', sourceLang)
  form.append('target_lang', targetLang)
  const res = await fetch('/api/translate/document/formatted', { method: 'POST', body: form })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new Error(detail)
  }
  const blob = await res.blob()
  const filename = parseFilename(res.headers.get('Content-Disposition'), 'translated.docx')
  return { blob, filename }
}

export function listMemory(params: {
  sourceLang?: string
  targetLang?: string
  query?: string
  limit?: number
  offset?: number
}): Promise<MemoryListResponse> {
  const search = new URLSearchParams()
  if (params.sourceLang) search.set('source_lang', params.sourceLang)
  if (params.targetLang) search.set('target_lang', params.targetLang)
  if (params.query) search.set('query', params.query)
  search.set('limit', String(params.limit ?? 50))
  search.set('offset', String(params.offset ?? 0))
  return request(`/api/memory?${search.toString()}`)
}

export function addManualEntry(entry: {
  source_text: string
  target_text: string
  source_lang: string
  target_lang: string
  document_title?: string
}): Promise<{ id: string }> {
  return request('/api/memory/entry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
}

export function deleteMemoryEntry(id: string): Promise<{ status: string }> {
  return request(`/api/memory/${id}`, { method: 'DELETE' })
}

export function previewDocumentPair(
  sourceFile: File,
  targetFile: File,
  sourceLang: string,
  targetLang: string,
): Promise<DocumentPairPreview> {
  const form = new FormData()
  form.append('source_file', sourceFile)
  form.append('target_file', targetFile)
  form.append('source_lang', sourceLang)
  form.append('target_lang', targetLang)
  return request('/api/memory/documents/preview', { method: 'POST', body: form })
}

export async function exportMemoryTmx(sourceLang?: string, targetLang?: string): Promise<Blob> {
  const search = new URLSearchParams()
  if (sourceLang) search.set('source_lang', sourceLang)
  if (targetLang) search.set('target_lang', targetLang)
  const query = search.toString()
  const res = await fetch(`/api/memory/export${query ? `?${query}` : ''}`)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new Error(detail)
  }
  return res.blob()
}

export function importMemoryTmx(
  file: File,
  sourceLang: string,
  targetLang: string,
  documentTitle: string,
): Promise<{ added_segments: number }> {
  const form = new FormData()
  form.append('file', file)
  form.append('source_lang', sourceLang)
  form.append('target_lang', targetLang)
  form.append('document_title', documentTitle)
  return request('/api/memory/import', { method: 'POST', body: form })
}

export function listGlossary(sourceLang?: string, targetLang?: string): Promise<GlossaryListResponse> {
  const search = new URLSearchParams()
  if (sourceLang) search.set('source_lang', sourceLang)
  if (targetLang) search.set('target_lang', targetLang)
  const query = search.toString()
  return request(`/api/glossary${query ? `?${query}` : ''}`)
}

export function addGlossaryEntry(entry: {
  source_term: string
  target_term: string
  source_lang: string
  target_lang: string
  note?: string
}): Promise<GlossaryEntry> {
  return request('/api/glossary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
}

export function deleteGlossaryEntry(id: string): Promise<{ status: string }> {
  return request(`/api/glossary/${id}`, { method: 'DELETE' })
}

export function commitDocumentPairs(
  pairs: DocumentPair[],
  sourceLang: string,
  targetLang: string,
  documentTitle: string,
): Promise<{ added_segments: number }> {
  return request('/api/memory/documents/commit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pairs,
      source_lang: sourceLang,
      target_lang: targetLang,
      document_title: documentTitle,
    }),
  })
}
