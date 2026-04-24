from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AarogyaAid API"
    DATABASE_URL: str
    GEMINI_API_KEY: str
    JWT_SECRET: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    GOOGLE_CLIENT_ID: str = ""
    CHROMA_PATH: str = "./chroma_db"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
