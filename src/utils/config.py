import os
from typing import Optional
# try:
#     from pydantic_settings import BaseSettings
# except ImportError:
#     from pydantic import BaseSettings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Azure OpenAI Configuration
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_deployment_name: str = "gpt-35-turbo"
    
    # Storage Configuration
    vector_store_path: str = "./data/vector_store"
    memory_db_path: str = "./data/memory.db"
    log_level: str = "INFO"
    
    # Memory Configuration
    max_tokens_short_term: int = 40000
    max_facts_long_term: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()