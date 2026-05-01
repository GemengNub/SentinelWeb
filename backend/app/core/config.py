"""
Application configuration using Pydantic Settings.
Compatible with both Pydantic v1 and v2.
"""
from functools import lru_cache
from typing import Optional
import os

# Handle both pydantic v1 and v2
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, Field
    PYDANTIC_V2 = False

# Load .env file manually for pydantic v1 compatibility
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Sentinel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/disaster_detector"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    
    # API Keys
    USGS_API_BASE_URL: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    OPENWEATHER_API_KEY: Optional[str] = None
    OPENWEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    NOAA_API_BASE_URL: str = "https://api.weather.gov"
    PAGASA_API_BASE_URL: str = "https://api.pagasa.dost.gov.ph"
    PAGASA_API_KEY: Optional[str] = None
    JMA_API_BASE_URL: str = "https://www.jma.go.jp/bosai/quake"
    FIRMS_API_BASE_URL: str = "https://firms2.modaps.eosdis.nasa.gov"
    FIRMS_API_KEY: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Alert thresholds
    EARTHQUAKE_LOW_THRESHOLD: float = 4.0
    EARTHQUAKE_MEDIUM_THRESHOLD: float = 5.5
    EARTHQUAKE_HIGH_THRESHOLD: float = 6.5
    EARTHQUAKE_CRITICAL_THRESHOLD: float = 7.5
    
    WIND_SPEED_LOW_THRESHOLD: float = 39.0  # mph
    WIND_SPEED_MEDIUM_THRESHOLD: float = 57.0
    WIND_SPEED_HIGH_THRESHOLD: float = 74.0
    WIND_SPEED_CRITICAL_THRESHOLD: float = 111.0
    
    RAINFALL_LOW_THRESHOLD: float = 2.5  # mm/hour
    RAINFALL_MEDIUM_THRESHOLD: float = 7.5
    RAINFALL_HIGH_THRESHOLD: float = 15.0
    RAINFALL_CRITICAL_THRESHOLD: float = 50.0

    # Alert lifecycle
    ALERT_AUTO_DEACTIVATE_DAYS: int = 7
    ALERT_DELETE_AFTER_DAYS: int = 90
    
    # Polling intervals (seconds)
    EARTHQUAKE_POLL_INTERVAL: int = 60
    WEATHER_POLL_INTERVAL: int = 60
    
    # Anomaly detection
    ANOMALY_WINDOW_SIZE: int = 24  # hours
    ANOMALY_DEVIATION_MULTIPLIER: float = 2.0
    
    # Prediction
    PREDICTION_LOOKBACK_HOURS: int = 48
    PREDICTION_FORECAST_HOURS: int = 6
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Notification (simulated)
    SMS_ENABLED: bool = True
    EMAIL_ENABLED: bool = True
    NOTIFICATION_LOG_PATH: str = "./logs/notifications.log"
    
    if PYDANTIC_V2:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": True,
        }
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
