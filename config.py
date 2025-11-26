from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME: str = os.getenv("MODEL_NAME") or "gemini-2.5-flash-preview-09-2025"
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "your-secret-key"

    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    class Config:
        extra = 'allow'  # Accept extra fields without error
        env_file = ".env"  # Optional: specify env file if used

settings = Settings()
