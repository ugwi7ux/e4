"""
Configuration management for the Telegram bot
Handles environment variables and default settings
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.telegram_token = self._get_env_var("TELEGRAM_BOT_TOKEN", "")
        self.openai_api_key = self._get_env_var("OPENAI_API_KEY", "")
        
        # Validate required tokens
        self._validate_config()
    
    def _get_env_var(self, key: str, default: str = "") -> str:
        """Get environment variable with fallback"""
        value = os.getenv(key, default)
        if value:
            logger.info(f"Loaded {key}: {'*' * (len(value) - 4)}{value[-4:]}")
        else:
            logger.warning(f"Environment variable {key} not found")
        return value
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN is required")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY is required")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        logger.info("Configuration validation successful")
    
    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(self.telegram_token and self.openai_api_key)
