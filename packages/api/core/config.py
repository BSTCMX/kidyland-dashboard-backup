"""
Configuration settings using Pydantic Settings.

Clean Architecture: Configuration in core module.
- Loads from environment variables and .env file
- Provides type-safe configuration with validation
- Dynamic helper functions for CORS and static files
- No hardcoding, fully responsive to environment
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Priority:
    1. Environment variables (highest priority)
    2. .env file (if exists)
    3. Default values (if provided)
    
    All settings are validated on instantiation.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars to prevent errors
    )
    
    # Required settings (must be provided via env or .env)
    DATABASE_URL: str
    SECRET_KEY: str
    
    # Optional settings with defaults
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str | None = None  # Comma-separated list for production
    STATIC_FILES_DIR: str = "./static"  # Directory for static files
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT.lower() == "test"


# Create settings instance (validated on import)
settings = Settings()


def get_cors_origins() -> List[str]:
    """
    Get CORS allowed origins based on environment.
    
    Clean Architecture: Configuration logic in core.config
    
    Behavior:
    - Development/Test: Returns ["*"] (allows all origins)
    - Production: Returns list from ALLOWED_ORIGINS env var (comma-separated)
    
    Returns:
        List of allowed origin strings
    """
    if settings.is_production and settings.ALLOWED_ORIGINS:
        # Production: parse comma-separated origins
        origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
        # Filter out empty strings
        return [origin for origin in origins if origin]
    
    # Development/Test: allow all origins
    return ["*"]


def get_static_files_dir() -> str:
    """
    Get static files directory path.
    
    Clean Architecture: Configuration logic in core.config
    
    Behavior:
    - Uses STATIC_FILES_DIR env var if set
    - Defaults to "./static" if not set
    - Can be overridden per environment
    
    Returns:
        Path to static files directory (relative or absolute)
    """
    return settings.STATIC_FILES_DIR
