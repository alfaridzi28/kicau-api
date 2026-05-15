import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secara eksplisit memuat .env dan meng-override variabel OS jika ada
load_dotenv(override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "KICAU API"
    SECRET_KEY: str = "supersecretkey_kicau_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
