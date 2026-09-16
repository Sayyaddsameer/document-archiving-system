import os
import logging
from dataclasses import dataclass

from app.vault_client import fetch_secrets

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool = False


def load_settings() -> Settings:
    """Load application settings, fetching sensitive values from Vault."""
    secrets = fetch_secrets()
    
    settings = Settings(
        db_host=os.environ.get("DB_HOST", "db"),
        db_port=int(os.environ.get("DB_PORT", "5432")),
        db_user=secrets["postgres_user"],
        db_password=secrets["postgres_password"],
        db_name=secrets["postgres_db"],
        minio_endpoint=os.environ.get("MINIO_ENDPOINT", "minio:9000"),
        minio_access_key=secrets["minio_root_user"],
        minio_secret_key=secrets["minio_root_password"],
        minio_bucket=os.environ.get("MINIO_BUCKET", "documents"),
    )
    
    logger.info("Configuration loaded successfully")
    return settings
