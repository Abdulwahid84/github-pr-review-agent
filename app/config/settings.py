from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # GitHub Configuration
    github_token: str = Field(default="", validation_alias="GITHUB_TOKEN")
    github_api_url: str = "https://api.github.com"
    
    # Gemini Configuration
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-1.5-flash"
    
    # API Configuration
    api_timeout: int = 30
    max_retries: int = 3
    
    # Application Configuration
    app_name: str = "GitHub PR Review Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate that all required settings are configured."""
    errors = []
    
    if not settings.github_token:
        errors.append("GITHUB_TOKEN environment variable is not set")
    
    if not settings.gemini_api_key:
        errors.append("GEMINI_API_KEY environment variable is not set")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(errors))

# Call validation on import (optional - uncomment if you want strict validation)
# validate_settings()