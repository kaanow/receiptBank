from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/receiptbank"
    session_secret: str = "change-me-in-production"
    session_cookie_secure: bool = False  # set True in production (HTTPS)
    file_storage_path: str = "./data/receipts"
    debug_ocr_secret: Optional[str] = None  # if set, POST /debug/ocr-probe accepts X-Debug-Secret for troubleshooting

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
