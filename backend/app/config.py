from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/receiptbank"
    session_secret: str = "change-me-in-production"
    file_storage_path: str = "./data/receipts"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
