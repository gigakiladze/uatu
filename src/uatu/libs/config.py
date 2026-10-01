from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    mongo_uri: str
    mongo_db_name: str
    qdrant_url: str
    qdrant_timeout_s: int = 10
    mongo_max_pool_size: int = 100
    mongo_min_pool_size: int = 10
    mongo_connect_timeout_ms: int = 10000
    mongo_app_name: str = "uatu"
    mongo_tz_aware: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"

    encryption_key: SecretStr 

    uatu_dev_project_id: str



    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: SecretStr | None = None
    LANGSMITH_PROJECT: str | None = None
    LANGSMITH_ENDPOINT: str | None = None



load_dotenv() 

settings = Settings()