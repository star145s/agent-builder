"""Configuration management for the miner API."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Server Configuration
    api_key: str = ""  # REQUIRED: Set via API_KEY environment variable
    port: int = 8001
    host: str = "0.0.0.0"
    environment: str = "production"  # Default to production for security
    
    # LLM Provider Configuration
    llm_provider: str = "openai"  # Options: "openai" or "vllm"
    
    # OpenAI Configuration
    openai_api_key: str = ""  # REQUIRED: Set in .env file
    openai_model: str = "gpt-4o-mini"
    openai_base_url: Optional[str] = None  # Optional custom base URL
    
    # vLLM Configuration (for self-hosted models)
    vllm_base_url: str = "http://localhost:8000/v1"  # vLLM server URL
    vllm_model: str = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
    vllm_api_key: str = ""  # Set via VLLM_API_KEY if using vLLM
    
    # Model Configuration
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Conversation History Settings
    max_conversation_messages: int = 10
    conversation_cleanup_days: int = 7
    smart_history_count: int = 5
    
    # Performance & Optimization Settings
    connection_pool_keepalive: int = 20
    connection_pool_max: int = 100
    connection_pool_keepalive_expiry: int = 30
    request_timeout: int = 60
    
    # Miner Configuration
    miner_name: str = "sample-miner"
    
    # API Settings
    debug: bool = False
    log_level: str = "INFO"
    
    # Gradio Test UI Configuration
    api_base_url: Optional[str] = None
    
    # Database Configuration (SQLite)
    database_url: str = "sqlite:///./data/miner_api.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle: int = 3600  # 1 hour
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',),
        extra='ignore'  # Allow extra fields without error
    )
    
    @property
    def get_model_name(self) -> str:
        """Get the appropriate model name based on provider."""
        if self.llm_provider == "openai":
            return self.openai_model
        elif self.llm_provider == "vllm":
            return self.vllm_model
        return self.openai_model
    
    @property
    def get_port(self) -> int:
        """Get the configured port."""
        return self.port if self.port else 8001
    
    @property
    def get_api_key(self) -> str:
        """Get the API key."""
        key = self.api_key
        
        # Security: Require API key to be set
        if not key or key == "":
            raise ValueError(
                "🔒 SECURITY ERROR: API_KEY must be set in environment variables!\n"
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                "Then set API_KEY=<your-key> in .env file or environment."
            )
        
        return key
    
    @property
    def get_vllm_base_url(self) -> str:
        """Get vLLM base URL."""
        return self.vllm_base_url or "http://localhost:8000/v1"


# Global settings instance
settings = Settings()
