export type MatchType = 'exact' | 'fuzzy'

export interface MatchInfo {
  type: MatchType
  similarity: number
  memory_source: string
  memory_target: string
  document_title: string
}

export interface Segment {
  source: string
  translation: string
  paragraph_index: number
  match: MatchInfo | null
}

export interface TranslateResponse {
  translated_text: string
  segments: Segment[]
}

export interface MemoryItem {
  id: string
  source_text: string
  target_text: string
  source_lang: string
  target_lang: string
  document_title: string
  created_at: string
}

export interface MemoryListResponse {
  items: MemoryItem[]
  total: number
}

export interface HealthResponse {
  status: string
  ollama_reachable: boolean
  chat_model: string
  embed_model: string
  chat_model_available: boolean
  embed_model_available: boolean
  memory_count: number
}

export interface DocumentPair {
  source_text: string
  target_text: string
}

export interface DocumentPairPreview {
  pairs: DocumentPair[]
  gap_count: number
}
