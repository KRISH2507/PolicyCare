import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AarogyaAid API"
    
    # These will be loaded automatically from a .env file or environment variables
    DATABASE_URL: str
    OPENAI_API_KEY: str
    JWT_SECRET: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    CHROMA_PATH: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields in the .env file
    )

settings = Settings()