"""
Configuration management for UACC Portal.

Handles environment-aware configuration:
- Local development: reads from ~/.config/uacc/.env (user config) or .env in project root
- Server deployment: reads from ~/config/env/uacc_db.env
- Environment variables always override file-based config
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings with environment-aware loading."""
    
    # Database configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "uacc_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    
    # Application configuration
    APP_ENV: str = "development"  # development, staging, production
    TEMP_DIR: str = "~/data/tmp"  # Temporary file storage
    
    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    
    model_config = SettingsConfigDict(
        env_file=None,  # We'll handle loading manually
        case_sensitive=True
    )


def load_config() -> Settings:
    """
    Load configuration from environment-aware sources.
    
    Priority order (lowest to highest, later loads override earlier):
    1. Default values
    2. Server config file ~/config/env/uacc_db.env (for deployment)
    3. Project root .env file (for development)
    4. User config file ~/.config/uacc/.env (for local development)
    5. Environment variables (highest priority, always override)
    """
    home_dir = Path.home()
    
    # Check for server config (lowest priority)
    server_config_path = home_dir / "config" / "env" / "uacc_db.env"
    if server_config_path.exists():
        load_dotenv(server_config_path, override=False)
    
    # Check for project root .env file
    project_root = Path(__file__).parent.parent.parent
    project_env_path = project_root / ".env"
    if project_env_path.exists():
        load_dotenv(project_env_path, override=False)
    
    # Check for user config file (higher priority for local dev)
    user_config_path = home_dir / ".config" / "uacc" / ".env"
    if user_config_path.exists():
        load_dotenv(user_config_path, override=False)
    
    # Environment variables are already loaded and will override file values
    # Create settings instance
    settings = Settings()
    
    # Expand ~ in TEMP_DIR
    settings.TEMP_DIR = os.path.expanduser(settings.TEMP_DIR)
    
    # Ensure temp directory exists
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    return settings


# Global settings instance
settings = load_config()

