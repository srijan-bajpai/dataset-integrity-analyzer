"""
DIA 2.0 Configuration — loaded from environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""
    base_dir: Path = Path(__file__).resolve().parent.parent
    storage_dir: Path = Path(os.getenv("DIA_STORAGE_DIR", str(base_dir / "storage")))
    database_url: str = os.getenv("DIA_DATABASE_URL", f"sqlite:///{base_dir / 'dia_v2.db'}")
    max_upload_size_mb: int = _env_int("DIA_MAX_UPLOAD_MB", 200)
    max_extracted_size_mb: int = _env_int("DIA_MAX_EXTRACTED_MB", 500)
    max_samples: int = _env_int("DIA_MAX_SAMPLES", 2000)
    max_member_size_mb: int = _env_int("DIA_MAX_IMAGE_MB", 25)
    shared_password: Optional[str] = os.getenv("DIA_SHARED_PASSWORD")
    environment: str = os.getenv("DIA_ENV", "development").lower()
    worker_poll_seconds: int = _env_int("DIA_WORKER_POLL_SECONDS", 2)
    cors_origins: str = os.getenv("DIA_CORS_ORIGINS", "*")
    supported_image_extensions: frozenset[str] = frozenset(
        {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    )

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def extract_dir(self) -> Path:
        return self.storage_dir / "extracted"

    @property
    def embeddings_dir(self) -> Path:
        return self.storage_dir / "embeddings"

    def ensure_directories(self) -> None:
        for path in (self.storage_dir, self.upload_dir, self.extract_dir, self.embeddings_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
