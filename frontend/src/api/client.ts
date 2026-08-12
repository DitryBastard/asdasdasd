import type {
  DocumentPair,
  DocumentPairPreview,
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

export function previewDocumentPair(sourceFile: File, targetFile: File): Promise<DocumentPairPreview> {
  const form = new FormData()
  form.append('source_file', sourceFile)
  form.append('target_file', targetFile)
  return request('/api/memory/documents/preview', { method: 'POST', body: form })
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
