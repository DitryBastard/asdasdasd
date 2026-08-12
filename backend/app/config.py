from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama connection. Ollama must be running locally (or reachable at this URL)
    # with the chat and embedding models already pulled.
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:14b-instruct"
    ollama_embed_model: str = "bge-m3"

    chroma_persist_dir: str = "./data/chroma"

    # Cosine similarity thresholds that decide how a translation-memory match
    # is used: below fuzzy it is ignored, between fuzzy and exact it is passed
    # to the model as a reference, at/above exact the stored translation is
    # reused as-is.
    exact_match_threshold: float = 0.98
    fuzzy_match_threshold: float = 0.75
    top_k_matches: int = 3

    # How many sentences are sent to the model in a single translation request.
    batch_size: int = 20

    # Max characters of document text sent to the chat model in a single
    # alignment call (see app/llm_alignment.py) - the model segments *and*
    # aligns a source/translation document pair in one step, rather than
    # pre-splitting into paragraphs with brittle heuristics first. Larger
    # means fewer chunks (better alignment quality, since the model sees
    # more context at once) at the cost of a longer prompt; this is sized
    # to comfortably fit an 8k+ context window with room for the response.
    llm_alignment_max_chars: int = 12000

    # Max horizontal gap (PDF points) between two characters before
    # pdfplumber treats them as separate words when extracting PDF text.
    # Lower catches tighter word gaps (fixes words getting glued together,
    # e.g. "wasdevelopedin") at the risk of splitting some legitimately
    # tight character pairs into extra spaces; this depends on the specific
    # PDF's font/kerning, so there is no one correct value - pdfplumber's
    # own default is 3.0, lowered here as a starting point since glued
    # words are a worse failure mode for both readability and matching
    # quality than an occasional stray space.
    pdf_text_x_tolerance: float = 1.5

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
