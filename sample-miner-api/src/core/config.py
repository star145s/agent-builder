"""Configuration management for the miner API."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Configuration
    llm_provider: str = "openai"  # Options: "openai" or "vllm"
    
    # OpenAI Configuration
    openai_api_key: str = ""  # Set in .env file
    openai_base_url: Optional[str] = None  # Optional custom base URL
    
    # vLLM Configuration (for self-hosted models)
    vllm_api_base: str = "http://localhost:8000/v1"  # vLLM server URL
    vllm_api_key: str = "EMPTY"  # vLLM usually doesn't require a key
    
    # Model Configuration
    model_name: str = "gpt-4o"  # For OpenAI or vLLM model name
    max_tokens: int = 4000
    temperature: float = 0.0
    
    # Miner Configuration
    miner_name: str = "sample-miner-gpt4o"
    miner_port: int = 8996
    host: str = "0.0.0.0"
    
    # Miner API Key (for authentication) - Set in .env file
    miner_api_key: str = ""
    
    # API Settings
    debug: bool = False
    log_level: str = "info"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',)
    )


# Global settings instance
settings = Settings()
