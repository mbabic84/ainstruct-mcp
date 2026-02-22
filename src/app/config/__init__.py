from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    openrouter_api_key: str = ""
    embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    embedding_dimensions: int = 4096

    api_keys: str = ""
    admin_api_key: str = ""

    db_path: str = "./data/documents.db"

    chunk_max_tokens: int = 400
    chunk_overlap_tokens: int = 50

    search_max_results: int = 5
    search_max_tokens: int = 2000

    host: str = "0.0.0.0"
    port: int = 8000

    jwt_secret_key: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    api_key_default_expiry_days: int | None = None

    @property
    def api_keys_list(self) -> list[str]:
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


settings = Settings()
