from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    app_name: str = "ICT ML Trading Bot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    
    mt5_login: int = 12345
    mt5_password: str = "password"
    mt5_server: str = "ICMarkets-Demo"
    mt5_path: Optional[str] = None
    mt5_timeout: int = 10000

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ict_trading_bot"
    db_user: str = "postgres"
    db_password: str = "postgres"
    database_url: Optional[str] = None
    
    @validator("database_url", pre=True, always=True)
    def assemble_db_url(cls, v, values):
        if v:
            return v
        return f"postgresql://{values.get('db_user')}:{values.get('db_password')}@{values.get('db_host')}:{values.get('db_port')}/{values.get('db_name')}"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    default_risk_percent: float = 1.0
    max_daily_loss_percent: float = 5.0
    trading_enabled: bool = False

settings = Settings()
