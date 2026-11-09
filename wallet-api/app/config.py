from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, read from environment variables (e.g. DATABASE_URL)."""

    database_url: str
    jwt_secret: str
    card_hash_secret: str  # key for the PAN hash, so it cannot be brute-forced
    jwt_ttl_minutes: int = 60
    fraud_address: str = "fraud:50051"
    fraud_timeout_seconds: float = 2.0
    fraud_api_key: str = "dev-wallet-key"
    buggy_mode: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
