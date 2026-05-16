"""
config.py — Centralized Configuration Management
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Security
    OPENAI_API_KEY: str = ""
    WEATHER_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    
    # Hybrid Providers
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GEMINI_API_KEY: str = ""
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json")
    
    # Provider Settings
    PRIMARY_LLM_MODEL: str = "llama-3.3-70b-versatile"
    FALLBACK_LLM_MODEL: str = "gemini-1.5-flash"
    STT_MODEL: str = "whisper-large-v3"
    TTS_VOICE: str = "en-US-AriaNeural"
    
    # Rate Limiting
    RATE_LIMIT_VOICE: str = "10/minute"
    RATE_LIMIT_TEXT: str = "30/minute"
    
    # Audio Limits
    MAX_AUDIO_SIZE_MB: int = 10
    ALLOWED_AUDIO_TYPES: list[str] = ["audio/wav", "audio/mpeg", "audio/webm", "audio/ogg", "audio/mp4"]
    
    # Caching
    CACHE_TTL_SECONDS: int = 600 # Increased for smarter flow
    MAX_CACHE_SIZE: int = 1000
    
    # Memory
    MAX_HISTORY_MESSAGES: int = 5
    
    # LLM Params
    MAX_TOKENS: int = 300
    TEMPERATURE: float = 0.7
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Initialize settings
settings = Settings()
