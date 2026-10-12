from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
from pathlib import Path
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelligent Logistics & Vehicle Routing Optimizer 2.0"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent.parent}/logistics.db"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent}/logistics.db"
    )
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]
    
    # Routing & Optimization Defaults
    DEFAULT_MAX_SPEED_KMH: float = 60.0
    DEFAULT_AVG_SPEED_KMH: float = 40.0
    DEFAULT_FUEL_PRICE_PER_LITER: float = 1.65
    DEFAULT_ELECTRICITY_COST_PER_KWH: float = 0.25
    DEFAULT_LATE_PENALTY_PER_MINUTE: float = 2.0
    
    # EV Defaults
    EV_MIN_RESERVE_SOC: float = 0.15 # 15% reserve
    EV_CONSUMPTION_KWH_PER_KM: float = 0.22
    
    # Model weights
    WEIGHT_DISTANCE: float = 0.25
    WEIGHT_TIME: float = 0.25
    WEIGHT_COST: float = 0.25
    WEIGHT_EMISSIONS: float = 0.15
    WEIGHT_PENALTY: float = 0.10

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        """Adapts Render PostgreSQL url to SQLAlchemy asyncpg format."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_db_url(self) -> str:
        """Adapts Render PostgreSQL url to sync format."""
        url = self.SYNC_DATABASE_URL
        if "sqlite" not in url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()
