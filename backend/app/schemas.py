from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = Field(min_length=2, max_length=10)
    target_lang: str = Field(min_length=2, max_length=10)


class MatchInfo(BaseModel):
    type: str
    similarity: float
    memory_source: str
    memory_target: str
    document_title: str


class SegmentOut(BaseModel):
    source: str
    translation: str
    paragraph_index: int
    match: MatchInfo | None = None
    warnings: list[str] = Field(default_factory=list)


class TranslateResponse(BaseModel):
    translated_text: str
    segments: list[SegmentOut]


class MemoryItemOut(BaseModel):
    id: str
    source_text: str
    target_text: str
    source_lang: str
    target_lang: str
    document_title: str
    created_at: str


class MemoryListResponse(BaseModel):
    items: list[MemoryItemOut]
    total: int


class ManualMemoryEntry(BaseModel):
    source_text: str
    target_text: str
    source_lang: str = Field(min_length=2, max_length=10)
    target_lang: str = Field(min_length=2, max_length=10)
    document_title: str = "Manual entry"


class DocumentPairPreviewResponse(BaseModel):
    pairs: list[dict[str, str]]
    gap_count: int


class DocumentPair(BaseModel):
    source_text: str
    target_text: str


class CommitDocumentPairsRequest(BaseModel):
    pairs: list[DocumentPair]
    source_lang: str = Field(min_length=2, max_length=10)
    target_lang: str = Field(min_length=2, max_length=10)
    document_title: str = "Untitled document"


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    chat_model: str
    embed_model: str
    chat_model_available: bool
    embed_model_available: bool
    memory_count: int


class GlossaryEntryOut(BaseModel):
    id: str
    source_term: str
    target_term: str
    source_lang: str
    target_lang: str
    note: str
    created_at: str


class GlossaryListResponse(BaseModel):
    items: list[GlossaryEntryOut]


class GlossaryEntryIn(BaseModel):
    source_term: str
    target_term: str
    source_lang: str = Field(min_length=2, max_length=10)
    target_lang: str = Field(min_length=2, max_length=10)
    note: str = ""
