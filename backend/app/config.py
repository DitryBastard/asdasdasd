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

    # Paragraph-alignment costs (see app/alignment.py). Higher gap_penalty
    # makes the aligner more reluctant to leave a paragraph unmatched;
    # higher merge_penalty makes it more reluctant to merge two paragraphs
    # on one side into one on the other. These are reasonable starting
    # points, not empirically tuned against real bge-m3 output - adjust if
    # real documents show the aligner being too eager/reluctant to skip.
    alignment_gap_penalty: float = 0.15
    alignment_merge_penalty: float = 0.03

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
