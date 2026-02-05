from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configuration from .env with default values
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore"
    )

    # Server
    server_name: str = Field(default="mcp-server", description="MCP server name")
    host: str = Field(default="0.0.0.0", description="Host binding for SSE")
    port: int = Field(default=8000, ge=1, le=65535, description="Port for SSE")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # HTTP Client
    http_timeout: float = Field(default=30.0, gt=0, description="HTTP requests timeout")
    http_max_connections: int = Field(default=100, ge=1, description="Max pool connections")

    # Tool limits
    max_text_length: int = Field(default=100_000, ge=1000, description="Max chars for process_text")
    max_url_content: int = Field(default=2000, ge=100, description="Max chars response fetch_url")

    # Feature flags
    enable_fetch_tool: bool = Field(default=True, description="Enable fetch_url tool")
    allowed_fetch_domains: list[str] | None = Field(
        default=None, 
        description="Allowed domains for fetch (None=all)"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
